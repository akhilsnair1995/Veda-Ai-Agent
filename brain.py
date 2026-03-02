# brain.py — HARDENED AGENTIC CORE
import ollama
from pathlib import Path
from rich.console import Console
import sys
import re
import json

BASE_DIR = Path(__file__).resolve().parent

# Ensure the project root is in sys.path
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from memory.history import get_recent_messages, save_message
from memory.semantic import SemanticMemory
from skills.skill_registry import SkillRegistry
from mcp.server_manager import MCPServerManager

console = Console()
OLLAMA_HOST_FILE = BASE_DIR / "config" / "colab_url.txt"

# ─────────────────────────────────────────────
# SYSTEM PROMPT — REINFORCED
# ─────────────────────────────────────────────
VEDA_SYSTEM_PROMPT = """You are Veda, an autonomous AI agent.
Your core mechanism is the TOOL/PARAMS loop.

FORMAT RULES:
1. When you need to act, you MUST use this format:
   TOOL: <name>
   PARAMS: {"arg": "value"}
2. You MUST provide the PARAMS block immediately after the TOOL line.
3. Use 'run_shell' for all terminal commands.
4. Stop generating text immediately after the closing '}'.

EXAMPLE:
User: check git status
Veda: I will check the repository status.
TOOL: run_shell
PARAMS: {"command": "git status"}
"""

class VedaBrain:
    def __init__(self, model: str = "veda"):
        self.model = model
        self.system_prompt = VEDA_SYSTEM_PROMPT
        self.semantic_memory = SemanticMemory()
        self.skill_registry = SkillRegistry()
        self.mcp_manager = MCPServerManager()
        self.init_errors = []

        host = self._get_host()
        self.client = ollama.Client(host=host)
        self.mcp_manager.start_all()

        self.init_errors.extend(self.skill_registry.init_errors)
        self.init_errors.extend(self.mcp_manager.init_errors)
        console.print("[bold green]✓ Veda Core Online.[/bold green]")

    def _get_host(self) -> str:
        if OLLAMA_HOST_FILE.exists():
            return OLLAMA_HOST_FILE.read_text().strip()
        import os
        return os.getenv("OLLAMA_HOST", "http://localhost:11434")

    def think(self, user_message: str, history: list = None) -> str:
        messages = self._build_messages(user_message, history)
        try:
            response = self.client.chat(
                model=self.model,
                messages=messages,
                options={"temperature": 0.0, "num_ctx": 8192}
            )
            return response["message"]["content"]
        except Exception as e:
            return f"Brain error: {e}"

    def _build_messages(self, user_message: str, history: list = None):
        if history:
            messages = history
        else:
            recent = get_recent_messages(limit=10)
            messages = list(recent)
            messages.append({"role": "user", "content": user_message})

        if not any(m.get('role') == 'system' for m in messages):
            system_content = self.system_prompt
            schemas = self.mcp_manager.get_all_tool_schemas()
            if schemas:
                tools_desc = "\n\nAVAILABLE TOOLS:\n" + "\n".join([f"- {s['name']}: {s.get('description', '')}" for s in schemas])
                system_content += tools_desc
            messages.insert(0, {"role": "system", "content": system_content})
        return messages

    def _handle_tool_calls(self, response: str, original_query: str) -> str:
        """Parses and executes tools with fallback logic."""
        # Find TOOL name - handle various spacings/formatting
        tool_match = re.search(r'TOOL:\s*([a-zA-Z0-9_]+)', response, re.IGNORECASE)
        if not tool_match:
            return response

        tool_name = tool_match.group(1).strip()
        
        # Find PARAMS - search for the first '{' and last '}' after the TOOL marker
        params = {}
        try:
            json_text_search = response[tool_match.end():]
            json_match = re.search(r'\{.*\}', json_text_search, re.DOTALL)
            if json_match:
                params = json.loads(json_match.group(0))
        except:
            params = {}

        # REINFORCEMENT: If tool is run_shell and params are missing, try to find the command in the text
        if tool_name == "run_shell" and not params.get("command"):
            cmd_match = re.search(r'["\'](git status|ls|pwd|dir)["\']', response)
            if cmd_match:
                params = {"command": cmd_match.group(1)}

        if not params and tool_name != "notes":
            result = f"Error: Tool '{tool_name}' missing parameters. Use PARAMS: {{'key': 'value'}}"
        else:
            console.print(f"[dim cyan]⚙ {tool_name}({params})[/dim cyan]")
            result = self.mcp_manager.call_tool(tool_name, params)

        # Interpret the result
        interpret_messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": f"Query: {original_query}\n\nTool '{tool_name}' returned:\n{result}\n\nProvide final answer."}
        ]
        
        final = self.client.chat(model=self.model, messages=interpret_messages, options={"temperature": 0.1})
        return final["message"]["content"]

    def stream_think(self, user_message: str, history: list = None):
        messages = self._build_messages(user_message, history)
        full_response = ""
        try:
            stream = self.client.chat(model=self.model, messages=messages, stream=True, options={"temperature": 0.0})
            for chunk in stream:
                token = chunk["message"]["content"]
                full_response += token
                yield token
                # Stop stream early if tool call is detected and closed
                if "TOOL:" in full_response.upper() and "}" in full_response:
                    break
        except Exception as e:
            yield f"\n✗ Error: {e}"

    def call_tool_sync(self, tool_call_text: str) -> str:
        return self._handle_tool_calls(tool_call_text, "Sync call")

    def add_mcp_server(self, name: str, command: list[str], description: str = ""):
        return self.mcp_manager.add_server(name, command, description)

    def create_skill(self, skill_code: str, filename: str) -> bool:
        skill_path = BASE_DIR / "skills" / filename
        skill_path.parent.mkdir(exist_ok=True)
        skill_path.write_text(skill_code, encoding="utf-8")
        self.skill_registry.reload_skills()
        return True

AIBrain = VedaBrain
