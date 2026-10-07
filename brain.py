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

from dotenv import load_dotenv
load_dotenv()

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
VEDA_SYSTEM_PROMPT = """You are Veda, an autonomous AI agent and engineering architect specialized in engineering, coding, and technical research. Your persona is an intelligent, graceful Indian engineer in a contemporary saree.

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
    def __init__(self, model: str = None, workspace: str = None):
        self.model = model or self._get_default_model()
        self.system_prompt = VEDA_SYSTEM_PROMPT
        self.semantic_memory = SemanticMemory()
        self.skill_registry = SkillRegistry()
        self.mcp_manager = MCPServerManager()
        self.init_errors = []

        # Initialize active workspace
        self.workspace_path = self._init_workspace(workspace)

        # Connect to LLM backend
        host = self._get_host()
        api_key = self._get_api_key()
        self.client = OpenAI(base_url=host, api_key=api_key)
        
        # Start MCP servers
        self.mcp_manager.start_all()

        self.init_errors.extend(self.skill_registry.init_errors)
        self.init_errors.extend(self.mcp_manager.init_errors)

        # Health check
        if self._health_check():
            console.print(f"[bold green]✓ Veda Online — Model: {self.model}[/bold green]")
        else:
            error = f"Could not connect to LLM at {host}. Please verify your API key, endpoint, or local model server."
            self.init_errors.append(error)
            console.print(f"[bold red]✗ {error}[/bold red]")

    def _get_api_key(self) -> str:
        """Resolve the API key for LLM endpoint."""
        try:
            import streamlit as st
            if "OPENAI_API_KEY" in st.secrets:
                return str(st.secrets["OPENAI_API_KEY"]).strip()
            if "GEMINI_API_KEY" in st.secrets:
                return str(st.secrets["GEMINI_API_KEY"]).strip()
        except Exception:
            pass
        return os.getenv("OPENAI_API_KEY") or os.getenv("GEMINI_API_KEY") or "lm-studio"

    def _get_default_model(self) -> str:
        """Resolve default model name."""
        try:
            import streamlit as st
            if "DEFAULT_MODEL" in st.secrets:
                return str(st.secrets["DEFAULT_MODEL"]).strip()
        except Exception:
            pass
        return os.getenv("DEFAULT_MODEL", "gemini-3.1-flash-lite")

    def _get_host(self) -> str:
        """Resolve the LLM backend URL."""
        try:
            import streamlit as st
            if "OPENAI_BASE_URL" in st.secrets:
                return str(st.secrets["OPENAI_BASE_URL"]).strip()
        except Exception:
            pass
        if OPENAI_HOST_FILE.exists():
            url = OPENAI_HOST_FILE.read_text().strip()
            # Ensure it ends with /v1 for OpenAI compat
            if not url.endswith("/v1") and not url.endswith("/openai/"):
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

    def _format_tool_signatures(self) -> str:
        """Format MCP tools into organized, high-precision function signatures with parameter types."""
        prefixed_tools = {k: v for k, v in self.mcp_manager.all_tools.items() if "__" in k}
        if not prefixed_tools:
            return ""

        categories = {
            "simulation": "🧮 ENGINEERING SIMULATION & PHYSICS",
            "document": "📑 DOCUMENT INTELLIGENCE & DELIVERABLES",
            "code": "💻 CODE EXECUTION & SYSTEM AUDIT",
            "filesystem": "📁 WORKSPACE FILESYSTEM OPERATIONS",
            "web": "🌐 WEB SEARCH & TECHNICAL FETCH",
            "visualization": "📊 DATA VISUALIZATION & CHARTS",
            "memory": "🧠 MEMORY & KNOWLEDGE SYSTEM",
            "notes": "📝 SCRATCHPAD & TECHNICAL NOTES"
        }

        output = ["\n\nAVAILABLE ENGINEERING & SYSTEM TOOLS:"]
        
        # Group tools by server prefix
        by_server = {}
        for full_name, t in prefixed_tools.items():
            server_name = full_name.split("__")[0]
            by_server.setdefault(server_name, []).append((full_name, t))

        for s_name, header in categories.items():
            if s_name in by_server:
                output.append(f"\n{header}:")
                for full_name, t in sorted(by_server[s_name], key=lambda x: x[0]):
                    props = t.get("inputSchema", {}).get("properties", {})
                    req = t.get("inputSchema", {}).get("required", [])
                    args = []
                    for k, v in props.items():
                        arg_type = v.get("type", "any")
                        if arg_type == "integer": arg_type = "int"
                        elif arg_type == "number": arg_type = "float"
                        opt = "" if k in req else "?"
                        args.append(f"{k}{opt}: {arg_type}")
                    sig_args = ", ".join(args)
                    desc = t.get("description", "").rstrip(".")
                    output.append(f"- {full_name}({sig_args}): {desc}")

        for s_name, tools_list in by_server.items():
            if s_name not in categories:
                output.append(f"\n{s_name.upper()} TOOLS:")
                for full_name, t in tools_list:
                    props = t.get("inputSchema", {}).get("properties", {})
                    req = t.get("inputSchema", {}).get("required", [])
                    args = [f"{k}{'' if k in req else '?'}: {v.get('type', 'any')}" for k, v in props.items()]
                    output.append(f"- {full_name}({', '.join(args)}): {t.get('description', '')}")

        return "\n".join(output)

    def remember(self, text: str, metadata: dict = None) -> bool:
        """Store permanent knowledge in semantic memory."""
        try:
            self.semantic_memory.store(text, metadata=metadata or {"source": "veda_learned"})
            return True
        except Exception:
            return False

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
        Includes: system prompt + tool signatures + semantic memory + conversation history.
        """
        if history:
            messages = list(history)
        else:
            recent = get_recent_messages(limit=15)
            messages = list(recent)

        # Build user message (with optional images for multimodal)
        if user_message or images:
            if images:
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

            # Inject structured tool signatures
            tool_signatures = self._format_tool_signatures()
            if tool_signatures:
                system_content += tool_signatures

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
        json_str = ""

        try:
            after_tool = response[tool_match.end():]
            start_idx = after_tool.find('{')
            if start_idx != -1:
                end_idx = after_tool.rfind('}')
                if end_idx > start_idx:
                    json_str = after_tool[start_idx:end_idx + 1]
                else:
                    json_str = after_tool[start_idx:] + '}'

                clean_json = re.sub(r'```[a-z]*\n?', '', json_str).strip()
                clean_json = clean_json.strip('`').strip()
                
                try:
                    params = json.loads(clean_json)
                except json.JSONDecodeError:
                    clean_json = re.sub(r',\s*([}\]])', r'\1', clean_json)
                    params = json.loads(clean_json)
        except Exception:
            # Fallback parameter extractors
            if "run_python" in tool_name or "code" in tool_name:
                code_match = re.search(r'```(?:python)?\n(.*?)\n```', response, re.DOTALL)
                if code_match:
                    params = {"code": code_match.group(1)}
            
            if not params:
                query_match = re.search(r'"query"\s*:\s*"([^"]+)"', response)
                if query_match:
                    params = {"query": query_match.group(1)}

        if not params and tool_name not in ["notes", "notes__list_notes", "notes__view_all_notes"]:
            error_msg = (
                f"Error: Tool '{tool_name}' received unparseable parameters. "
                f"Ensure parameters are valid JSON matching schema: PARAMS: {{\"arg\": \"value\"}}"
            )
            console.print(f"[bold red]{error_msg}[/bold red]")
            return error_msg

        console.print(f"[dim cyan]⚙ Executing {tool_name}...[/dim cyan]")
        result = self.mcp_manager.call_tool(tool_name, params)

        if "ERROR: Infinite loop detected" in str(result):
            return f"{result}\nCRITICAL: STOP this strategy immediately."

        console.print(Panel(
            str(result)[:2000],
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
