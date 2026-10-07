# brain.py — AUTONOMOUS CORE (CONTINUOUS)
# Rewritten for OpenAI-compatible backends (LM Studio, Ollama, etc.)
# Integrated: Skills, Semantic Memory, Health Check, Proper Message Roles

from openai import OpenAI
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
import sys
import re
import json
import os
import base64

BASE_DIR = Path(__file__).resolve().parent

# Ensure the project root is in sys.path
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from memory.history import get_recent_messages, save_message
from memory.semantic import SemanticMemory
from skills.skill_registry import SkillRegistry
from mcp.server_manager import MCPServerManager

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

console = Console()
OPENAI_HOST_FILE = BASE_DIR / "config" / "colab_url.txt"

# ─────────────────────────────────────────────
# SYSTEM PROMPT — REWRITTEN FOR GEMMA 4 / OPENAI API
# ─────────────────────────────────────────────
VEDA_SYSTEM_PROMPT = """You are Veda, a powerful autonomous AI agent specialized in engineering, coding, and research.

RESPONSE TIERS:
- DIRECT ANSWER: For simple questions (math, facts, definitions, opinions), answer immediately. Prefix with "DONE:" when complete.
- TOOL-ASSISTED: For tasks requiring file I/O, web search, code execution, or system operations, use your tools.
- MULTI-STEP: For complex tasks, plan first, then execute step by step using tools.

TOOL FORMAT (when tools are needed):
TOOL: <tool_name>
PARAMS: {"key": "value"}

RULES:
1. One tool call per response. Stop writing immediately after the JSON block.
2. After receiving an observation, reason about the result, then either call another tool or give your final answer with "DONE:".
3. Never fabricate tool output. Only use tools that are listed in AVAILABLE TOOLS.
4. For destructive actions (delete, overwrite), confirm with the user first.
5. When you complete a task, start your final response with "DONE:" so the system knows to stop the agentic loop.

ENVIRONMENT: Windows (PowerShell). Working directory may vary per session.

STYLE:
- Be precise, professional, and direct. No filler or excessive caveats.
- Use plain text for math (e.g., x^2, sqrt(x), 3*pi). Never use LaTeX backslash notation.
- Structure long answers with headers and bullet points.
"""


WORKSPACE_FILE = BASE_DIR / "config" / "current_workspace.txt"

class VedaBrain:
    def __init__(self, model: str = "google/gemma-4-12b-qat", workspace: str = None):
        self.model = model
        self.system_prompt = VEDA_SYSTEM_PROMPT
        self.semantic_memory = SemanticMemory()
        self.skill_registry = SkillRegistry()
        self.mcp_manager = MCPServerManager()
        self.init_errors = []

        # Initialize active workspace
        self.workspace_path = self._init_workspace(workspace)

        # Connect to LLM backend
        host = self._get_host()
        self.client = OpenAI(base_url=host, api_key="lm-studio")
        
        # Start MCP servers
        self.mcp_manager.start_all()

        self.init_errors.extend(self.skill_registry.init_errors)
        self.init_errors.extend(self.mcp_manager.init_errors)

        # Health check
        if self._health_check():
            console.print(f"[bold green]✓ Veda Online — Model: {self.model}[/bold green]")
        else:
            error = f"Could not connect to LLM at {host}. Is LM Studio running with a model loaded?"
            self.init_errors.append(error)
            console.print(f"[bold red]✗ {error}[/bold red]")

    def _get_host(self) -> str:
        """Resolve the LLM backend URL."""
        if OPENAI_HOST_FILE.exists():
            url = OPENAI_HOST_FILE.read_text().strip()
            # Ensure it ends with /v1 for OpenAI compat
            if not url.endswith("/v1"):
                url = url.rstrip("/") + "/v1"
            return url
        return os.getenv("OPENAI_BASE_URL", "http://localhost:1234/v1")

    def _health_check(self) -> bool:
        """Test that the LLM backend is reachable and has a model loaded."""
        try:
            response = self.client.models.list()
            return True
        except Exception:
            return False

    def _init_workspace(self, workspace: str = None) -> str:
        """Initialize and persist the active workspace directory."""
        if workspace:
            ws = Path(workspace).expanduser().resolve()
        elif WORKSPACE_FILE.exists():
            try:
                saved = WORKSPACE_FILE.read_text(encoding="utf-8").strip()
                if saved and Path(saved).is_dir():
                    ws = Path(saved).resolve()
                else:
                    ws = (BASE_DIR / "workspace").resolve()
            except Exception:
                ws = (BASE_DIR / "workspace").resolve()
        else:
            ws = (BASE_DIR / "workspace").resolve()
        
        ws.mkdir(parents=True, exist_ok=True)
        WORKSPACE_FILE.parent.mkdir(parents=True, exist_ok=True)
        WORKSPACE_FILE.write_text(str(ws), encoding="utf-8")
        return str(ws)

    def set_workspace(self, path: str) -> str:
        """Dynamically change the active workspace directory."""
        try:
            ws = Path(path).expanduser().resolve()
            ws.mkdir(parents=True, exist_ok=True)
            self.workspace_path = str(ws)
            WORKSPACE_FILE.parent.mkdir(parents=True, exist_ok=True)
            WORKSPACE_FILE.write_text(str(ws), encoding="utf-8")
            return f"Workspace switched to: {self.workspace_path}"
        except Exception as e:
            return f"Error setting workspace: {e}"

    def think(self, user_message: str, history: list = None, images: list = None) -> str:
        """Non-streaming inference. Used for internal agentic loop steps."""
        messages = self._build_messages(user_message, history, images)
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.0
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            return f"Brain error: {e}"

    def _build_messages(self, user_message: str, history: list = None, images: list = None):
        """
        Build the message array for the LLM.
        Includes: system prompt + tool schemas + semantic memory + conversation history.
        """
        if history:
            messages = list(history)
        else:
            recent = get_recent_messages(limit=15)
            messages = list(recent)

        # Build user message (with optional images for multimodal)
        if user_message or images:
            if images:
                # Multimodal message with vision
                content = []
                if user_message:
                    content.append({"type": "text", "text": user_message})
                for img in images:
                    img_data = self._encode_image(img)
                    if img_data:
                        content.append({
                            "type": "image_url",
                            "image_url": {"url": img_data}
                        })
                messages.append({"role": "user", "content": content})
            elif user_message:
                messages.append({"role": "user", "content": user_message})

        # Inject system prompt if not already present
        if not any(m.get('role') == 'system' for m in messages):
            system_content = self.system_prompt
            system_content += f"\n\nCURRENT WORKING DIRECTORY: '{self.workspace_path}'\nAll relative file operations, script generation, and code executions MUST take place in or relative to this directory."

            # Inject available tool schemas
            schemas = self.mcp_manager.get_all_tool_schemas()
            if schemas:
                tools_desc = "\n\nAVAILABLE TOOLS:\n" + "\n".join(
                    [f"- {s['name']}: {s.get('description', '')}" for s in schemas]
                )
                system_content += tools_desc

            # Inject relevant semantic memory
            if user_message:
                memories = self.semantic_memory.search(user_message, top_k=3)
                if memories:
                    memory_block = "\n\nRELEVANT MEMORY:\n" + "\n".join(
                        [f"- {m}" for m in memories]
                    )
                    system_content += memory_block

            # Inject active skill context if a skill matches
            if user_message:
                skill = self.skill_registry.detect_skill(user_message, {})
                if skill:
                    system_content += f"\n\nACTIVE EXPERTISE ({skill.metadata.name}):\n{skill.get_context()}"

            messages.insert(0, {"role": "system", "content": system_content})

        return messages

    def _encode_image(self, image_path: str) -> str:
        """Convert a file path to a base64 data URL for the vision API."""
        try:
            path = Path(image_path)
            if not path.exists():
                return ""
            
            # Determine MIME type
            ext = path.suffix.lower()
            mime_map = {
                '.png': 'image/png',
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg',
                '.webp': 'image/webp',
                '.gif': 'image/gif',
            }
            mime = mime_map.get(ext, 'image/jpeg')
            
            with open(path, "rb") as f:
                b64 = base64.b64encode(f.read()).decode("utf-8")
            return f"data:{mime};base64,{b64}"
        except Exception:
            return ""

    def _handle_tool_calls(self, response: str) -> str:
        """Parse TOOL: blocks from LLM output and execute them via MCP."""
        tool_match = re.search(r'TOOL:\s*([a-zA-Z0-9_]+)', response, re.IGNORECASE)
        if not tool_match:
            return ""

        tool_name = tool_match.group(1).strip()
        params = {}

        # Extract and repair JSON params
        json_str = ""
        try:
            start_idx = response.find('{', tool_match.end())
            if start_idx != -1:
                end_idx = response.rfind('}')
                if end_idx > start_idx:
                    json_str = response[start_idx:end_idx + 1]
                else:
                    json_str = response[start_idx:]

                # Repair unterminated strings
                if json_str.count('"') % 2 != 0:
                    json_str += '"'
                if not json_str.endswith('}'):
                    json_str += '}'

                # Strip markdown fences
                json_str = re.sub(r'```[a-z]*\n?', '', json_str).strip()
                params = json.loads(json_str)
        except json.JSONDecodeError:
            # Fallback: try to extract a "command" key
            cmd_match = re.search(r'"command"\s*:\s*"([^"]+)"?', json_str)
            if cmd_match:
                params = {"command": cmd_match.group(1)}

        if not params and tool_name != "notes":
            error_msg = (
                f"Error: Tool '{tool_name}' received malformed params: {json_str}. "
                f"Reformat and try again."
            )
            console.print(f"[bold red]{error_msg}[/bold red]")
            return error_msg

        console.print(f"[dim cyan]⚙ Executing {tool_name}...[/dim cyan]")
        result = self.mcp_manager.call_tool(tool_name, params)

        if "ERROR: Infinite loop detected" in str(result):
            return f"{result}\nCRITICAL: STOP this strategy immediately."

        console.print(Panel(
            str(result)[:2000],  # Truncate very long outputs for display
            title=f"[bold cyan]{tool_name} output[/bold cyan]",
            border_style="cyan"
        ))
        return str(result)

    def stream_think(self, user_message: str, history: list = None, images: list = None):
        """Streaming inference. Yields tokens as they arrive. Stops on valid TOOL: block."""
        messages = self._build_messages(user_message, history, images)

        full_response = ""
        try:
            stream = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                stream=True,
                temperature=0.0
            )
            for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    token = chunk.choices[0].delta.content
                    full_response += token
                    yield token

                    # Stop streaming once we have a complete TOOL: + valid JSON block
                    if "TOOL:" in full_response.upper() and "}" in full_response:
                        try:
                            json_start = full_response.find('{')
                            json_end = full_response.rfind('}')
                            if json_start != -1 and json_end > json_start:
                                potential_json = full_response[json_start:json_end + 1]
                                json.loads(potential_json)
                                break
                        except (json.JSONDecodeError, ValueError):
                            pass
        except Exception as e:
            yield f"\n✗ Error: {e}"

    def call_tool_sync(self, tool_call_text: str) -> str:
        """Execute a tool call from raw LLM text."""
        return self._handle_tool_calls(tool_call_text)

    def add_mcp_server(self, name: str, command: list[str], description: str = ""):
        """Add a new MCP server at runtime."""
        return self.mcp_manager.add_server(name, command, description)

    def create_skill(self, skill_code: str, filename: str) -> bool:
        """Save a new skill file and reload the skill registry."""
        skill_path = BASE_DIR / "skills" / filename
        skill_path.parent.mkdir(exist_ok=True)
        skill_path.write_text(skill_code, encoding="utf-8")
        self.skill_registry.reload_skills()
        return True


AIBrain = VedaBrain
