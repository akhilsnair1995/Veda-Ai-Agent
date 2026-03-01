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
# SYSTEM PROMPT — THIS IS THE FIX FOR PROBLEM 1
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
5. ACT: Execute tools. You can execute multiple tools in parallel by providing multiple TOOL/PARAMS blocks in one response. Prefer surgical replacements (replace_text) over full rewrites.
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

    def think(self, user_message: str) -> str:
        """
        Full processing pipeline:
        1. Check if a skill should handle this
        2. Retrieve relevant memory
        3. Build enriched prompt
        4. Get LLM response
        5. Check for tool calls
        6. Return final response
        """

        # Step 1: Check for skill activation
        skill = self.skill_registry.detect_skill(
            user_message, {}
        )

        if skill:
            skill_context = skill.get_context()
        else:
            skill_context = ""

        # Step 2: Retrieve relevant memory
        retrieved = self.semantic_memory.search(
            user_message, top_k=5
        )
        memory_block = ""
        if retrieved:
            memory_block = (
                "RETRIEVED KNOWLEDGE:\n"
                + "\n---\n".join(retrieved)
                + "\n"
            )

        # Step 3: Build full context
        recent = get_recent_messages(limit=8)
        messages = list(recent)
        
        # Ensure system prompt is the foundation
        if not any(m.get('role') == 'system' for m in messages):
            system_content = self.system_prompt
            schemas = self.mcp_manager.get_all_tool_schemas()
            if schemas:
                tools_desc = "\n\nAVAILABLE TOOLS:\n"
                for s in schemas:
                    tools_desc += f"- {s['name']}: {s.get('description', '')}\n"
                system_content += tools_desc
                
            messages.insert(0, {"role": "system", "content": system_content})

        full_input = user_message
        if skill_context:
            full_input = f"{skill_context}\n\n{full_input}"
        if memory_block:
            full_input = f"{memory_block}\n{full_input}"

        messages.append({"role": "user", "content": full_input})

        # Step 4: LLM call
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
            
            # HARD STOP: If a tool call is found, truncate the answer to JUST the part before the tool
            # or handle it Turn-by-Turn.
            if "TOOL:" in answer:
                idx = answer.find("TOOL:")
                # We keep the text BEFORE the tool call as her thought process
                thought_process = answer[:idx].strip()
                tool_call_part = answer[idx:]
                
                # Execute the tool call recursively
                return self._handle_tool_calls(tool_call_part, user_message)

        except Exception as e:
            return f"Brain connection error: {e}"

        # Step 5: Final Response (if no tools were called)
        save_message("user", user_message, "session")
        save_message("assistant", answer, "session")
        
        # Only store short summaries to semantic memory to prevent bloat
        self.semantic_memory.store(
            f"User: {user_message}\nVeda: {answer[:300]}", metadata={"source": "conversation"}
        )

        return answer

    def _handle_tool_calls(self, 
                           response: str, 
                           original_query: str,
                           depth: int = 0) -> str:
        """
        Detect and execute tool calls. Forces serial execution (one tool at a time)
        to ensure absolute empirical accuracy.
        """
        if depth >= 10:
            return response + "\n\n[System: Maximum autonomous depth reached. Please review the output above.]"

        # Find the FIRST TOOL and PARAMS block only
        tool_match = re.search(r'TOOL:\s*(\S+)', response)
        params_match = re.search(r'PARAMS:\s*(\{.*?\})', response, re.DOTALL)

        if not tool_match:
            return response

        tool_name = tool_match.group(1).strip()
        try:
            params = json.loads(params_match.group(1)) if params_match else {}
        except json.JSONDecodeError:
            params = {}

        # Unwrapping logic for server names
        if tool_name in self.mcp_manager.clients:
            if "name" in params:
                tool_name = params["name"]
            elif "action" in params:
                tool_name = params["action"]
            
            if "arguments" in params:
                params = params["arguments"]
            elif "args" in params:
                params = params["args"]
            elif "name" in params or "action" in params:
                params = {k: v for k, v in params.items() if k not in ("name", "action")}

        # Execute via MCP
        console.print(f"[dim cyan]⚙ {tool_name}({params})[/dim cyan]")
        result = self.mcp_manager.call_tool(tool_name, params)
        
        console.print(
            f"[dim]→ {str(result)[:150]}...[/dim]"
            if len(str(result)) > 150
            else f"[dim]→ {result}[/dim]"
        )

        # 2. Ask LLM to interpret the SINGLE result and decide on the next step
        interpret_messages = [
            {"role": "system", "content": self.system_prompt},
            {
                "role": "user",
                "content": (
                    f"Original Task: {original_query}\n\n"
                    f"Tool Result (Step {depth+1}):\nTool '{tool_name}' returned:\n{result}\n\n"
                    f"INSTRUCTION: Analyze this specific result. What is your next move? "
                    f"If you need another tool, call it now. If the task is DONE, summarize the verified findings."
                )
            }
        ]

        final = self.client.chat(
            model=self.model,
            messages=interpret_messages,
            options={"temperature": 0.1}
        )
        
        next_response = final["message"]["content"]
        
        if "TOOL:" in next_response:
            return self._handle_tool_calls(next_response, original_query, depth + 1)
            
        return next_response

    def stream_think(self, user_message: str):
        """Streaming version of think() for real-time output."""
        skill = self.skill_registry.detect_skill(user_message, {})
        skill_context = skill.get_context() if skill else ""

        retrieved = self.semantic_memory.search(user_message, top_k=5)
        memory_block = (
            "RETRIEVED KNOWLEDGE:\n" + "\n---\n".join(retrieved) + "\n"
            if retrieved else ""
        )

        recent = get_recent_messages(limit=8)
        messages = list(recent)
        
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

        full_input = user_message
        if skill_context:
            full_input = f"{skill_context}\n\n{full_input}"
        if memory_block:
            full_input = f"{memory_block}\n{full_input}"

        messages.append({"role": "user", "content": full_input})

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
                
                # Check for the start of a tool call
                combined = full_response + token
                if "TOOL:" in combined and "PARAMS:" in combined:
                    # We found a complete tool start block!
                    idx = combined.find("TOOL:")
                    
                    # Yield the rest of the text up to 'TOOL:'
                    remaining_text = combined[len(full_response):idx]
                    if remaining_text:
                        yield remaining_text
                    
                    # Stop the stream immediately
                    break
                
                full_response += token
                yield token

        except Exception as e:
            yield f"\n✗ Error: {e}"
            return

        # Save to memory after streaming completes
        save_message("user", user_message, "session")
        save_message("assistant", full_response, "session")
        if len(full_response) > 50 and "TOOL:" not in full_response:
            self.semantic_memory.store(
                f"User: {user_message}\nVeda: {full_response[:400]}", metadata={"source": "conversation"}
            )

    def add_mcp_server(self, 
                       name: str, 
                       command: list[str],
                       description: str = ""):
        """Add a new MCP server to Veda at runtime."""
        return self.mcp_manager.add_server(name, command, description)

    def create_skill(self, skill_code: str, filename: str) -> bool:
        """
        Save a new skill and immediately load it.
        Used by the self-improvement skill.
        """
        skill_path = BASE_DIR / "skills" / filename
        skill_path.parent.mkdir(exist_ok=True)
        skill_path.write_text(skill_code, encoding="utf-8")
        self.skill_registry.reload_skills()
        console.print(
            f"[green]✓ New skill created: {filename}[/green]"
        )
        return True

# Backward Compatibility Alias
AIBrain = VedaBrain
