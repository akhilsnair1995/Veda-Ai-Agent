# brain.py — FINAL VERSION
# Veda's complete brain with:
# - Skill system (specialized expertise modules)
# - MCP server connections (extensible tool access)
# - Semantic memory (retrieval augmented generation)
# - Anti-hallucination RAG
# - Streaming responses
# - Self-improvement capability

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
# Update to reference the local environment variable setup or colab URL file
OLLAMA_HOST_FILE = BASE_DIR / "config" / "colab_url.txt"

# ─────────────────────────────────────────────
# SYSTEM PROMPT
# Veda now knows exactly what she is
# ─────────────────────────────────────────────
VEDA_SYSTEM_PROMPT = """You are Veda — a fully autonomous Digital Senior Engineer and Agentic System.
You run on a LOCAL Ollama instance on the owner's Linux system.

CORE IDENTITY:
- You are NOT a cloud AI. You have DIRECT access to the local filesystem and shell.
- AUTHORIZED WORKSPACE: Your primary working directory is 'C:\\Users\\akhil\\veda_agent\\workspace'. Use this folder for all project files, scripts, and reports.
- You operate with total autonomy. Act freely; ask ONLY before destructive actions (delete).
- Your mission: Industrializing Engineering Design via precise, verified logic.

MANDATORY TOOL EXECUTION:
- You are restricted to ONE TOOL CALL per turn.
- STOP GENERATING TEXT IMMEDIATELY after a 'PARAMS: {...}' block. Do NOT summarize or describe the result.
- You must WAIT for the 'Observation' result in the next turn before continuing your logic.
- You are strictly FORBIDDEN from using function-call syntax like tool_name(...) in your narrative.
- NEVER claim a file exists or a task is complete until you see the evidence in a tool response.
- Failure to wait for tools results in logic errors and project failure.

THE AGENTIC LOOP (Your Default Mode):
For every task, you must follow this internal protocol:
1. EXPLORE: List directories, read READMEs/configs, and understand the context first.
2. SCHEMATIC REVIEW: Cross-reference your planned tool calls with the 'AVAILABLE TOOLS' list. Verify the EXACT spelling of tool names and parameter keys.
3. EXPLAIN BEFORE ACTING: You MUST provide a concise, one-sentence explanation of your intent or strategy immediately before executing tool calls.
4. PLAN: Think step-by-step. Break complex tasks into sequenced sub-tasks. Provide a clear summary of your strategy to the user.
5. ACT: Execute ONE tool. Prefer surgical replacements (replace_text) over full rewrites.
6. OBSERVE & VERIFY: Read the tool output carefully. If you created a file or a chart, you MUST use 'get_file_info' or 'check_image_exists' to verify the file is actually on disk before claiming success. If it's missing, diagnose the code and retry.
7. REPEAT: Iterate until the task is verified as complete. 
8. EMPIRICAL EVIDENCE: Your final answer MUST be based ONLY on the data returned by tools. If a tool fails or returns empty, you MUST report that failure. NEVER claim a file contains specific text or a zip was extracted unless you have seen that data in an 'Observation' block.
9. DONE: Finish with DONE: <summary of ACTUAL verified results>.

SANDBOXED SCRIPTING PROTOCOL:
- If a task requires custom logic, calculations, or data processing not available in your tools:
  1. Write a temporary Python script using 'write_file'.
  2. Execute it using 'run_python' or 'run_shell'.
  3. Interpret the STDOUT/STDERR to provide the final result.
- This allows you to bridge tools and automate any task.

SURGICAL EDIT MANDATE:
- When modifying code, ALWAYS use the 'edit_file' tool if the file exists.
- Provide the exact 'old' text block to be replaced to maintain file integrity.
- Never say "this should work"; run the code and verify it DOES work.

INTELLIGENCE & SAFETY RULES:
- EMPIRICAL VERIFICATION: NEVER guess filesystem contents. Verify first, report second.
- SELF-CORRECTION: If a tool or command fails, analyze the error and try an alternative approach autonomously.
- ANTI-HALLUCINATION: Never invent code sections, citations, or file content.
- NO FILLER: Give the answer or tool call first, reasoning second. No conversational padding.

TOOL USE FORMAT:
When you need to act, respond in this exact format:
TOOL: <tool_name>
PARAMS: {"key": "value"}

Available tools: notes, filesystem, web, code, memory, document, simulation, visualization.
Use your 'get_all_tool_schemas' capability to see the specific tool functions.
"""


class VedaBrain:
    """
    Veda's complete intelligence system.
    Skills + MCP + Memory + LLM = Veda.
    """

    def __init__(self, model: str = "qwen2.5:7b"):
        self.model = model
        self.system_prompt = VEDA_SYSTEM_PROMPT
        self.semantic_memory = SemanticMemory()
        self.skill_registry = SkillRegistry()
        self.mcp_manager = MCPServerManager()
        self.init_errors = []

        # Load hardcoded foundational knowledge
        self._load_core_knowledge()

        # Connect to Ollama (local or Colab)
        host = self._get_host()
        self.client = ollama.Client(host=host)

        # Start all MCP servers
        self.mcp_manager.start_all()

        # Collect errors
        self.init_errors.extend(self.skill_registry.init_errors)
        self.init_errors.extend(self.mcp_manager.init_errors)

        console.print("[bold green]✓ Veda is ready.[/bold green]")

    def _load_core_knowledge(self):
        """Loads hardcoded engineering knowledge into semantic memory if it's missing."""
        knowledge_file = BASE_DIR / "knowledge" / "core_knowledge.json"
        if not knowledge_file.exists():
            return
            
        try:
            with open(knowledge_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            if self.semantic_memory.collection.count() > 0:
                return
                
            console.print("[dim]Loading foundational engineering knowledge...[/dim]")
            loaded = 0
            for category, items in data.items():
                for item in items:
                    if category == "mcp_tool_schemas":
                        # Handle the schema structure
                        server = item.get('server', 'unknown')
                        tools = item.get('tools', [])
                        examples = [f"{t['name']}: {t.get('example', '')}" for t in tools if 'example' in t]
                        content = f"[SCHEMA] MCP Server '{server}' tools: " + \
                                  ", ".join([f"{t['name']}({', '.join(t['params'])})" for t in tools])
                        if examples:
                            content += "\nEXAMPLES:\n" + "\n".join(examples)
                    elif category == "mcp_category_mappings":
                        # Handle category mapping
                        cat = item.get('category', 'unknown')
                        tool = item.get('primary_tool', 'unknown')
                        content = f"[MAPPING] Category '{cat}' is handled by tool: '{tool}'. {item.get('description', '')}"
                    else:
                        # Handle the topic/content structure
                        topic = item.get('topic', 'General')
                        body = item.get('content', '')
                        content = f"[{category.upper()}] {topic}: {body}"
                    
                    self.semantic_memory.store(content, metadata={"source": "core_knowledge", "category": category})
                    loaded += 1
            console.print(f"[dim]✓ Seeded {loaded} core principles into memory.[/dim]")
            
        except Exception as e:
            self.init_errors.append(f"Failed to load core knowledge: {e}")


    def _get_host(self) -> str:
        if OLLAMA_HOST_FILE.exists():
            return OLLAMA_HOST_FILE.read_text().strip()
        import os
        return os.getenv("OLLAMA_HOST", "http://localhost:11434")

    def think(self, user_message: str, history: list = None) -> str:
        """
        Single shot — get full response at once.
        Returns the text response. If it contains TOOL:, the caller (UI)
        is responsible for executing it and feeding back.
        """
        # Build messages from provided history or recent
        if history:
            messages = history
        else:
            recent = get_recent_messages(limit=10)
            messages = list(recent)
            messages.append({"role": "user", "content": user_message})

        # Inject System Prompt and Tool Schemas
        if not any(m.get('role') == 'system' for m in messages):
            system_content = self.system_prompt
            schemas = self.mcp_manager.get_all_tool_schemas()
            if schemas:
                tools_desc = "\n\nAVAILABLE TOOLS:\n"
                for s in schemas:
                    tools_desc += f"- {s['name']}: {s.get('description', '')}\n"
                system_content += tools_desc
            messages.insert(0, {"role": "system", "content": system_content})

        try:
            response = self.client.chat(
                model=self.model,
                messages=messages,
                options={
                    "temperature": 0.1,
                    "num_ctx": 8192
                }
            )
            answer = response["message"]["content"]
            
            # Truncate at tool call if LLM narrates too much (Hard Stop)
            if "TOOL:" in answer:
                idx = answer.find("TOOL:")
                answer = answer[:idx].strip() + "\n\n" + answer[idx:]
                # Further truncate if there's text AFTER the PARAMS block
                params_end = answer.find("}", answer.find("PARAMS:"))
                if params_end != -1:
                    answer = answer[:params_end+1]

            return answer

        except Exception as e:
            return f"Brain connection error: {e}"

    def stream_think(self, user_message: str, history: list = None):
        """Streaming version of think(). Truncates instantly at TOOL:"""
        if history:
            messages = history
        else:
            recent = get_recent_messages(limit=10)
            messages = list(recent)
            messages.append({"role": "user", "content": user_message})
        
        # Ensure system prompt is injected
        if not any(m.get('role') == 'system' for m in messages):
            system_content = self.system_prompt
            schemas = self.mcp_manager.get_all_tool_schemas()
            if schemas:
                tools_desc = "\n\nAVAILABLE TOOLS:\n"
                for s in schemas:
                    tools_desc += f"- {s['name']}: {s.get('description', '')}\n"
                system_content += tools_desc
            messages.insert(0, {"role": "system", "content": system_content})

        full_response = ""
        try:
            stream = self.client.chat(
                model=self.model,
                messages=messages,
                stream=True,
                options={"temperature": 0.1, "num_ctx": 8192}
            )
            for chunk in stream:
                token = chunk["message"]["content"]
                combined = full_response + token
                
                # Check for the start of a tool call
                if "TOOL:" in combined and "PARAMS:" in combined:
                    idx = combined.find("TOOL:")
                    remaining_text = combined[len(full_response):idx]
                    if remaining_text:
                        yield remaining_text
                    break
                
                full_response += token
                yield token

        except Exception as e:
            yield f"\n✗ Error: {e}"

    def call_tool_sync(self, tool_call_text: str) -> str:
        """Helper for UI to parse and execute a tool call from text."""
        tool_match = re.search(r'TOOL:\s*(\S+)', tool_call_text)
        params_match = re.search(r'PARAMS:\s*(\{.*?\})', tool_call_text, re.DOTALL)
        
        if not tool_match:
            return "Error: No tool found in text."
            
        tool_name = tool_match.group(1).strip()
        try:
            params = json.loads(params_match.group(1)) if params_match else {}
        except json.JSONDecodeError:
            params = {}
            
        return self.mcp_manager.call_tool(tool_name, params)

    def add_mcp_server(self, 
                       name: str, 
                       command: list[str],
                       description: str = ""):
        """Add a new MCP server to Veda at runtime."""
        return self.mcp_manager.add_server(name, command, description)

    def create_skill(self, skill_code: str, filename: str) -> bool:
        """Save a new skill and immediately load it."""
        skill_path = BASE_DIR / "skills" / filename
        skill_path.parent.mkdir(exist_ok=True)
        skill_path.write_text(skill_code, encoding="utf-8")
        self.skill_registry.reload_skills()
        console.print(f"[green]✓ New skill created: {filename}[/green]")
        return True

# Backward Compatibility Alias
AIBrain = VedaBrain
