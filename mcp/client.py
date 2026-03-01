# mcp/client.py
# Veda's MCP client — built from scratch, no SDK dependencies.
# Connects to any MCP server via stdio or SSE transport.
# Discovers tools automatically and exposes them to Veda's tool registry.

import json
import subprocess
import threading
import queue
import uuid
import requests
import time
from pathlib import Path
from typing import Any, Optional
from rich.console import Console

console = Console()


class MCPError(Exception):
    """Raised when an MCP operation fails."""
    pass


class StdioTransport:
    """
    Communicates with an MCP server over stdin/stdout.
    The server runs as a subprocess.
    This is the most common transport for local MCP servers.
    """

    def __init__(self, command: list[str], env: dict = None):
        self.command = command
        self.env = env
        self.process = None
        self._response_queue = queue.Queue()
        self._reader_thread = None
        self._running = False

    def start(self):
        """Start the MCP server subprocess."""
        import os
        env = {**os.environ, **(self.env or {})}

        self.process = subprocess.Popen(
            self.command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            env=env
        )

        self._running = True
        self._reader_thread = threading.Thread(
            target=self._read_loop,
            daemon=True
        )
        self._reader_thread.start()
        console.print(
            f"[dim]MCP server started: "
            f"{' '.join(self.command[:2])}...[/dim]"
        )

    def _read_loop(self):
        """
        Background thread that continuously reads 
        server output and queues responses.
        """
        while self._running and self.process.poll() is None:
            try:
                line = self.process.stdout.readline()
                if line.strip():
                    response = json.loads(line.strip())
                    self._response_queue.put(response)
            except json.JSONDecodeError:
                pass  # Skip non-JSON lines (like debug output)
            except Exception:
                break

    def send(self, message: dict) -> dict:
        """Send a JSON-RPC message and wait for the response."""
        if not self.process or self.process.poll() is not None:
            raise MCPError("MCP server is not running")

        # Send message
        line = json.dumps(message) + "\n"
        self.process.stdin.write(line)
        self.process.stdin.flush()

        # Wait for matching response (by id)
        msg_id = message.get("id")
        timeout = 30  # seconds

        start = time.time()
        while time.time() - start < timeout:
            try:
                response = self._response_queue.get(timeout=1)
                if response.get("id") == msg_id:
                    return response
                else:
                    # Put it back if it's not for us
                    self._response_queue.put(response)
            except queue.Empty:
                continue

        raise MCPError(f"Timeout waiting for response to message {msg_id}")

    def stop(self):
        """Stop the MCP server subprocess."""
        self._running = False
        if self.process:
            self.process.terminate()
            self.process.wait()


class SSETransport:
    """
    Communicates with an MCP server over HTTP/SSE.
    Used for remote MCP servers or servers that run as daemons.
    """

    def __init__(self, base_url: str, api_key: str = None):
        self.base_url = base_url.rstrip("/")
        self.headers = {"Content-Type": "application/json"}
        if api_key:
            self.headers["Authorization"] = f"Bearer {api_key}"

    def send(self, message: dict) -> dict:
        """Send a JSON-RPC message via HTTP POST."""
        try:
            response = requests.post(
                f"{self.base_url}/message",
                json=message,
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            raise MCPError(f"HTTP transport error: {e}")

    def stop(self):
        pass  # No process to stop for HTTP transport


class MCPClient:
    """
    Veda's universal MCP client.
    Connects to an MCP server, discovers its capabilities,
    and makes them available as callable tools.
    """

    def __init__(self, transport):
        self.transport = transport
        self.server_info = {}
        self.available_tools = {}
        self.available_resources = {}
        self._initialized = False
        self._msg_id = 0

    @classmethod
    def from_stdio(cls, command: list[str], env: dict = None):
        """Create a client that talks to a local subprocess server."""
        transport = StdioTransport(command, env)
        transport.start()
        return cls(transport)

    @classmethod
    def from_sse(cls, url: str, api_key: str = None):
        """Create a client that talks to a remote HTTP server."""
        transport = SSETransport(url, api_key)
        return cls(transport)

    def _next_id(self) -> int:
        self._msg_id += 1
        return self._msg_id

    def _send(self, method: str, params: dict = None) -> Any:
        """Send a JSON-RPC request and return the result."""
        message = {
            "jsonrpc": "2.0",
            "id": self._next_id(),
            "method": method,
            "params": params or {}
        }

        response = self.transport.send(message)

        if "error" in response:
            raise MCPError(
                f"MCP error {response['error']['code']}: "
                f"{response['error']['message']}"
            )

        return response.get("result", {})

    def initialize(self) -> dict:
        """
        Perform the MCP handshake.
        Must be called before any other method.
        """
        result = self._send("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "roots": {"listChanged": False},
                "sampling": {}
            },
            "clientInfo": {
                "name": "Veda",
                "version": "1.0.0"
            }
        })

        # Send initialized notification
        notif = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized",
            "params": {}
        }
        self.transport.send(notif)

        self.server_info = result
        self._initialized = True

        server_name = result.get('serverInfo', {}).get('name', 'unknown')
        console.print(
            f"[green]✓ MCP server connected: {server_name}[/green]"
        )
        return result

    def list_tools(self) -> list[dict]:
        """Get all tools this server offers."""
        result = self._send("tools/list")
        tools = result.get("tools", [])

        # Cache tools for use by Veda's tool registry
        for tool in tools:
            self.available_tools[tool["name"]] = tool

        return tools

    def call_tool(self, tool_name: str, arguments: dict) -> str:
        """
        Call a tool on the MCP server.
        Returns the text result.
        """
        if tool_name not in self.available_tools:
            raise MCPError(
                f"Tool '{tool_name}' not found. "
                f"Available: {list(self.available_tools.keys())}"
            )

        result = self._send("tools/call", {
            "name": tool_name,
            "arguments": arguments
        })

        # Extract text content from result
        content = result.get("content", [])
        if isinstance(content, list):
            return "\n".join(
                item.get("text", "") 
                for item in content 
                if item.get("type") == "text"
            )
        return str(result)

    def list_resources(self) -> list[dict]:
        """Get all resources this server exposes."""
        result = self._send("resources/list")
        return result.get("resources", [])

    def read_resource(self, uri: str) -> str:
        """Read a resource by its URI."""
        result = self._send("resources/read", {"uri": uri})
        contents = result.get("contents", [])
        return "\n".join(
            c.get("text", "") for c in contents
        )

    def disconnect(self):
        """Cleanly disconnect from the server."""
        self.transport.stop()
