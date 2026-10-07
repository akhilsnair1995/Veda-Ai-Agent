# mcp/server_manager.py
# Manages all of Veda's MCP servers.
# Reads server config, starts servers, connects clients,
# and registers all discovered tools with Veda's tool registry.

import json
import yaml
import sys
from pathlib import Path
from typing import Optional
from rich.console import Console

# Add parent to path to ensure we can import mcp
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from mcp.client import MCPClient

console = Console()
CONFIG_FILE = BASE_DIR / "config" / "mcp_servers.yaml"


class MCPServerManager:
    """
    The central hub for all of Veda's MCP connections.
    
    On startup: reads config, starts all configured servers,
    connects clients, discovers tools, registers them all.
    
    At runtime: routes tool calls to the right server,
    handles reconnection if a server died,
    allows adding new servers without restarting Veda.
    """

    def __init__(self):
        self.clients: dict[str, MCPClient] = {}
        # Maps tool_name -> server_name for routing
        self.tool_routing: dict[str, str] = {}
        self.all_tools: dict[str, dict] = {}
        self.init_errors: list[str] = []
        self._last_calls: list[str] = [] # Track last few calls to prevent loops

    def load_config(self) -> dict:
        """
        Load server configuration from YAML file.
        Creates a default config if none exists or if paths are stale.
        """
        if not CONFIG_FILE.exists():
            self._create_default_config()
        else:
            try:
                data = yaml.safe_load(CONFIG_FILE.read_text())
                servers = data.get("servers", {}) if isinstance(data, dict) else {}
                stale = False
                for s_cfg in servers.values():
                    cmd = s_cfg.get("command", [])
                    if cmd and isinstance(cmd, list) and len(cmd) >= 2:
                        if not Path(cmd[0]).exists() or not Path(cmd[1]).exists():
                            stale = True
                            break
                if stale:
                    console.print("[dim yellow]Detected stale paths in MCP config. Regenerating dynamically...[/dim yellow]")
                    self._create_default_config()
            except Exception:
                self._create_default_config()
        return yaml.safe_load(CONFIG_FILE.read_text())

    def _create_default_config(self):
        """Create the default MCP server config."""
        CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
        # Use the current python executable (virtual environment)
        python_exec = sys.executable
        
        default = {
            "servers": {
                "notes": {
                    "command": [
                        python_exec,
                        str(BASE_DIR / "mcp/servers/notes_server.py")
                    ],
                    "enabled": True,
                    "description": "Veda's personal notes system"
                },
                "filesystem": {
                    "command": [
                        python_exec,
                        str(BASE_DIR / "mcp/servers/filesystem_server.py")
                    ],
                    "enabled": True,
                    "description": "File system operations"
                },
                "web": {
                    "command": [
                        python_exec,
                        str(BASE_DIR / "mcp/servers/web_server.py")
                    ],
                    "enabled": True,
                    "description": "Web search and fetch"
                },
                "code": {
                    "command": [
                        python_exec,
                        str(BASE_DIR / "mcp/servers/code_server.py")
                    ],
                    "enabled": True,
                    "description": "Code execution and analysis"
                },
                "memory": {
                    "command": [
                        python_exec,
                        str(BASE_DIR / "mcp/servers/memory_server.py")
                    ],
                    "enabled": True,
                    "description": "Veda's memory system"
                },
                "document": {
                    "command": [
                        python_exec,
                        str(BASE_DIR / "mcp/servers/document_server.py")
                    ],
                    "enabled": True,
                    "description": "PDF parsing and document intelligence"
                },
                "visualization": {
                    "command": [
                        python_exec,
                        str(BASE_DIR / "mcp/servers/visualization_server.py")
                    ],
                    "enabled": True,
                    "description": "Chart and graph generation"
                },
                "system_apps": {
                    "command": [
                        python_exec,
                        str(BASE_DIR / "mcp/servers/system_apps_server.py")
                    ],
                    "enabled": True,
                    "description": "Control Windows applications"
                },
                "google_apps": {
                    "command": [
                        python_exec,
                        str(BASE_DIR / "mcp/servers/google_apps_server.py")
                    ],
                    "enabled": True,
                    "description": "Google Workspace integration"
                },
                "simulation": {
                    "command": [
                        python_exec,
                        str(BASE_DIR / "mcp/servers/simulation_server.py")
                    ],
                    "enabled": True,
                    "description": "Engineering calculations and physics"
                }
            }
        }
        CONFIG_FILE.write_text(yaml.dump(default, default_flow_style=False))
        console.print(f"[dim]Created MCP config: {CONFIG_FILE}[/dim]")

    def start_all(self):
        """Start all enabled MCP servers and register their tools."""
        config = self.load_config()
        servers = config.get("servers", {})

        for name, server_config in servers.items():
            if not server_config.get("enabled", True):
                continue
            try:
                self._connect_server(name, server_config)
            except Exception as e:
                error_msg = f"Could not start MCP server '{name}': {e}"
                self.init_errors.append(error_msg)
                console.print(f"[yellow]⚠ {error_msg}[/yellow]")

        total_tools = len(self.all_tools)
        console.print(
            f"[green]✓ MCP ready: {len(self.clients)} servers, "
            f"{total_tools} tools available[/green]"
        )

    def _connect_server(self, name: str, config: dict):
        """Connect to a single MCP server and register its tools."""
        command = config["command"]

        # Support both stdio and SSE transports
        if config.get("type") == "sse":
            client = MCPClient.from_sse(
                config["url"],
                config.get("api_key")
            )
        else:
            client = MCPClient.from_stdio(
                command,
                config.get("env")
            )

        client.initialize()
        tools = client.list_tools()

        # Register all tools with routing table
        for tool in tools:
            tool_name = tool["name"]
            # Prefix with server name to avoid conflicts
            full_name = f"{name}__{tool_name}"
            self.tool_routing[full_name] = name
            self.tool_routing[tool_name] = name  # Also register without prefix
            self.all_tools[full_name] = tool
            self.all_tools[tool_name] = tool

        self.clients[name] = client
        console.print(
            f"[dim]  ✓ {name}: {len(tools)} tools[/dim]"
        )

    def call_tool(self, tool_name: str, params: dict) -> str:
        """
        Route a tool call to the correct MCP server.
        Includes a Fuzzy Router to handle common category-level hallucinations.
        """
        # 1. Fuzzy Routing Logic
        fuzzy_map = {
            "web": "web__search",
            "code": "code__run_python",
            "filesystem": "filesystem__list_directory",
            "pdf": "document__read_pdf",
            "chart": "visualization__generate_chart",
            "plot": "visualization__generate_chart",
            "calc": "simulation__calc_psychrometrics",
            "unzip": "filesystem__unzip_file",
            "extract_zip": "filesystem__unzip_file"
        }
        
        target_tool = tool_name.lower().strip()
        if target_tool in fuzzy_map:
            console.print(f"[dim yellow]Fuzzy routing '{target_tool}' -> '{fuzzy_map[target_tool]}'[/dim yellow]")
            target_tool = fuzzy_map[target_tool]

        # 2. REPETITION BREAKER
        call_sig = f"{target_tool}:{json.dumps(params, sort_keys=True)}"
        if self._last_calls.count(call_sig) >= 2:
            self._last_calls.clear() # Reset after breaking
            return f"ERROR: Infinite loop detected for tool '{target_tool}'. You have already called this tool with these exact parameters. DO NOT retry. Change your strategy or ask the user for clarification."
        
        self._last_calls.append(call_sig)
        if len(self._last_calls) > 5:
            self._last_calls.pop(0)

        # 3. Standard Routing
        server_name = self.tool_routing.get(target_tool)
        if not server_name:
            # Check if it was provided without prefix but is in routing
            if target_tool in self.tool_routing:
                server_name = self.tool_routing[target_tool]
            else:
                return f"No MCP server found for tool: {tool_name}"

        client = self.clients.get(server_name)
        if not client:
            return f"MCP server '{server_name}' not connected"

        # Strip server prefix if present
        clean_name = target_tool.replace(f"{server_name}__", "")

        # 4. CLEANUP: Hallucinated keys and variations
        if isinstance(params, dict):
            # Remove 'server' key if hallucinated
            if "server" in params:
                params = {k: v for k, v in params.items() if k != "server"}

            # Alias for 'run_python' code
            if clean_name == "run_python" and "code" not in params:
                if "python_code" in params:
                    params["code"] = params.get("python_code")

        try:
            return client.call_tool(clean_name, params)
        except Exception as e:
            return f"MCP tool error ({target_tool}): {e}"

    def get_all_tool_schemas(self) -> list[dict]:
        """Return schemas for all available tools across all servers."""
        return list(self.all_tools.values())

    def add_server(self, 
                   name: str, 
                   command: list[str],
                   description: str = "") -> bool:
        """
        Add and connect a new MCP server at runtime.
        No restart required. Tools available immediately.
        """
        config = self.load_config()
        config["servers"][name] = {
            "command": command,
            "enabled": True,
            "description": description
        }
        CONFIG_FILE.write_text(
            yaml.dump(config, default_flow_style=False)
        )

        try:
            self._connect_server(name, config["servers"][name])
            console.print(f"[green]✓ New MCP server added: {name}[/green]")
            return True
        except Exception as e:
            console.print(f"[red]✗ Failed to add server: {e}[/red]")
            return False

    def disconnect_all(self):
        """Cleanly shut down all MCP connections."""
        for name, client in self.clients.items():
            try:
                client.disconnect()
            except Exception:
                pass
        self.clients.clear()
