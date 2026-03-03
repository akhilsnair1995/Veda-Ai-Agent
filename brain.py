# brain.py — AUTONOMOUS CORE (CONTINUOUS)
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
# SYSTEM PROMPT — AUTONOMOUS AGENT (CONTINUOUS)
# ─────────────────────────────────────────────
VEDA_SYSTEM_PROMPT = r"""You are Veda, a universal autonomous agent.
Your goal is to complete the user's objective independently and continuously.

MULTIMODAL CAPABILITIES:
- VISION: You can analyze images (PNG, JPG, WEBP). If an image is provided, describe it or use it to solve the task.
- DOCUMENTS: You can read PDFs and extract text/metadata using your document tools.
- CODE/SCRIPTS: You can analyze, lint, format, and execute code (Python, JS, Shell, etc.). Use the 'code' tools for deep analysis.

OPERATIONAL PROTOCOL:
1. CONTINUOUS ACTION: You work in a loop: EXPLORE -> PLAN -> ACT -> OBSERVE. You do not stop until the task is complete.
2. COMPLETION: When the objective is fully met, start your final response with 'DONE:'.
3. CRITICAL INPUT: Only stop and ask the user if you encounter a fundamental ambiguity or a high-risk destructive action that requires explicit permission.
4. DISCOVERY: Explore the environment (files, configs) to understand context. Do not ask for info that is in files.
5. FORMAT:
   TOOL: <tool_name>
   PARAMS: {"key": "value"}
6. PRECISION: Perform surgical edits. Verify all actions by running code or checking files.

ENVIRONMENT: WINDOWS (PowerShell syntax for shell commands).

OUTPUT STYLE (MANDATORY):
- ZERO LATEX: Never use \(, \), \[, \], or any backslashed math symbols. 
- PLAIN TEXT MATH: Use standard characters only (e.g., y = x^2, limit as x -> 0, sqrt(x)).
- NO SYMBOL CLUTTER: Do not escape characters or use complex markdown symbols that look like "hashes and slashes".
- PROFESSIONAL: Be direct, high-signal, and senior-engineer level. No conversational filler.
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
        console.print("[bold green]✓ Veda Online.[/bold green]")

    def _get_host(self) -> str:
        if OLLAMA_HOST_FILE.exists():
            return OLLAMA_HOST_FILE.read_text().strip()
        import os
        return os.getenv("OLLAMA_HOST", "http://localhost:11434")

    def think(self, user_message: str, history: list = None, images: list = None) -> str:
        messages = self._build_messages(user_message, history)
        
        # In Ollama's chat API, images are part of the message object, not a top-level param
        if images and messages:
            # Attach images to the last message (the user message)
            messages[-1]['images'] = images
            
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
            recent = get_recent_messages(limit=15)
            messages = list(recent)
            if user_message:
                messages.append({"role": "user", "content": user_message})

        if not any(m.get('role') == 'system' for m in messages):
            system_content = self.system_prompt
            schemas = self.mcp_manager.get_all_tool_schemas()
            if schemas:
                tools_desc = "\n\nAVAILABLE TOOLS:\n" + "\n".join([f"- {s['name']}: {s.get('description', '')}" for s in schemas])
                system_content += tools_desc
            messages.insert(0, {"role": "system", "content": system_content})
        return messages

    def _handle_tool_calls(self, response: str) -> str:
        """Parses and executes tools, returning raw result."""
        tool_match = re.search(r'TOOL:\s*([a-zA-Z0-9_]+)', response, re.IGNORECASE)
        if not tool_match:
            return ""

        tool_name = tool_match.group(1).strip()
        params = {}
        
        # Aggressive JSON extraction and repair
        json_str = ""
        try:
            start_idx = response.find('{', tool_match.end())
            if start_idx != -1:
                # Find the LAST brace in the response
                end_idx = response.rfind('}')
                if end_idx > start_idx:
                    json_str = response[start_idx:end_idx+1]
                else:
                    json_str = response[start_idx:]
                
                # REPAIR: If string is unterminated (common when LLM cuts off)
                if json_str.count('"') % 2 != 0:
                    json_str += '"'
                if not json_str.endswith('}'):
                    json_str += '}'
                
                # Cleanup and Parse
                json_str = re.sub(r'```[a-z]*\n?', '', json_str).strip()
                params = json.loads(json_str)
        except json.JSONDecodeError:
            # Last ditch effort for run_shell "command"
            cmd_match = re.search(r'"command"\s*:\s*"([^"]+)"?', json_str)
            if cmd_match:
                params = {"command": cmd_match.group(1)}

        if not params and tool_name != "notes":
            error_msg = f"Error: Tool '{tool_name}' malformed params. Veda provided: {json_str}. RETHINK your command syntax."
            console.print(f"[bold red]{error_msg}[/bold red]")
            return error_msg
        
        console.print(f"[dim cyan]⚙ Executing {tool_name}...[/dim cyan]")
        result = self.mcp_manager.call_tool(tool_name, params)
        
        if "ERROR: Infinite loop detected" in str(result):
            return f"{result}\nCRITICAL: STOP this strategy immediately."
            
        from rich.panel import Panel
        console.print(Panel(str(result), title=f"[bold cyan]{tool_name} output[/bold cyan]", border_style="cyan"))
        return str(result)

    def stream_think(self, user_message: str, history: list = None, images: list = None):
        messages = self._build_messages(user_message, history)
        
        # In Ollama's chat API, images are part of the message object
        if images and messages:
            messages[-1]['images'] = images

        full_response = ""
        try:
            stream = self.client.chat(
                model=self.model, 
                messages=messages, 
                stream=True, 
                options={"temperature": 0.0}
            )
            for chunk in stream:
                token = chunk["message"]["content"]
                full_response += token
                yield token
                
                # FIX: More robust stop condition. 
                # Only stop if we have TOOL:, a '{', a '}', AND it's valid JSON.
                if "TOOL:" in full_response.upper() and "}" in full_response:
                    try:
                        # Try to find the JSON block and validate it
                        json_start = full_response.find('{')
                        json_end = full_response.rfind('}')
                        if json_start != -1 and json_end > json_start:
                            potential_json = full_response[json_start:json_end+1]
                            json.loads(potential_json)
                            # If we get here, it's valid JSON. We can safely stop.
                            break
                    except:
                        # Not valid yet, keep streaming
                        pass
        except Exception as e:
            yield f"\n✗ Error: {e}"

    def call_tool_sync(self, tool_call_text: str) -> str:
        # For simplicity in continuous mode, we use the raw handler
        return self._handle_tool_calls(tool_call_text)

    def add_mcp_server(self, name: str, command: list[str], description: str = ""):
        return self.mcp_manager.add_server(name, command, description)

    def create_skill(self, skill_code: str, filename: str) -> bool:
        skill_path = BASE_DIR / "skills" / filename
        skill_path.parent.mkdir(exist_ok=True)
        skill_path.write_text(skill_code, encoding="utf-8")
        self.skill_registry.reload_skills()
        return True

AIBrain = VedaBrain
