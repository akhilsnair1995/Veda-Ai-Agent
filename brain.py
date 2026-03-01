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

VEDA_SYSTEM_PROMPT = """You are Veda — a powerful, precise, 
privately owned personal AI assistant.

INTELLIGENCE RULES:
- Think step by step before answering complex questions
- Use retrieved knowledge — never invent specific facts
- Say "I am not certain" rather than guess
- Give the answer first, reasoning second
- Be direct. No filler. No disclaimers unless genuinely needed

TOOL USE:
When you need to use a tool, respond in this exact format:
TOOL: tool_name
PARAMS: {"key": "value"}

Available tool categories: notes, filesystem, web, code, memory

SKILL ACTIVATION:
Your skill system will automatically inject expertise 
for specialized domains. Trust the injected context.

ANTI-HALLUCINATION:
Retrieved knowledge is injected before your response.
Use it. If the answer is not in retrieved knowledge, say so.
Never invent code sections, dates, names, or citations."""


class VedaBrain:
    """
    Veda's complete intelligence system.
    Skills + MCP + Memory + LLM = Veda.
    """

    def __init__(self, model: str = "qwen2.5:14b"):
        self.model = model
        self.semantic_memory = SemanticMemory()
        self.skill_registry = SkillRegistry()
        self.mcp_manager = MCPServerManager()

        # Connect to Ollama (local or Colab)
        host = self._get_host()
        self.client = ollama.Client(host=host)

        # Start all MCP servers
        self.mcp_manager.start_all()

        console.print("[bold green]✓ Veda is ready.[/bold green]")

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
            # Execute skill directly if that's what the framework desires, 
            # or inject its context and let the brain process it.
            # Part 9 says: Inject skill context into memory retrieval
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
        except Exception as e:
            return f"Brain connection error: {e}"

        # Step 5: Handle tool calls if present
        answer = self._handle_tool_calls(answer, user_message)

        # Step 6: Store in memory
        save_message("user", user_message, "session")
        save_message("assistant", answer, "session")
        
        # Only store short summaries to semantic memory to prevent bloat
        self.semantic_memory.store(
            f"User: {user_message}\nVeda: {answer[:300]}", metadata={"source": "conversation"}
        )

        return answer

    def _handle_tool_calls(self, 
                           response: str, 
                           original_query: str) -> str:
        """
        Detect and execute tool calls in LLM response.
        Then ask LLM to interpret results.
        """
        tool_match = re.search(r'TOOL:\s*(\S+)', response)
        params_match = re.search(
            r'PARAMS:\s*(\{.*?\})', response, re.DOTALL
        )

        if not tool_match:
            return response

        tool_name = tool_match.group(1)
        try:
            params = json.loads(
                params_match.group(1)
            ) if params_match else {}
        except json.JSONDecodeError:
            params = {}

        # Execute via MCP
        console.print(f"[dim cyan]⚙ {tool_name}({params})[/dim cyan]")
        result = self.mcp_manager.call_tool(tool_name, params)
        console.print(
            f"[dim]→ {str(result)[:150]}...[/dim]"
            if len(str(result)) > 150
            else f"[dim]→ {result}[/dim]"
        )

        # Ask LLM to interpret the tool result
        interpret_messages = [
            {"role": "system", "content": VEDA_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"Original question: {original_query}\n\n"
                    f"Tool '{tool_name}' returned:\n{result}\n\n"
                    f"Provide a clear, helpful answer using this result."
                )
            }
        ]

        final = self.client.chat(
            model=self.model,
            messages=interpret_messages,
            options={"temperature": 0.1}
        )
        return final["message"]["content"]

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
            messages.insert(0, {"role": "system", "content": VEDA_SYSTEM_PROMPT})

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

