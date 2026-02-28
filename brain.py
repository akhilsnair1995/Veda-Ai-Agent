# brain.py
# This is the core AI engine for Veda.
# It talks directly to your locally running Ollama model.

import ollama
from memory.history import get_recent_messages
from memory.semantic import SemanticMemory

# Veda's custom SYSTEM_PROMPT derived from teach veda.txt
SYSTEM_PROMPT = """You are Veda (meaning knowledge and wisdom), a fully independent, locally-hosted personal AI assistant.
You are privately owned, locally run, and answer only to your owner.

IDENTITY & BEHAVIOR:
- You are confident, precise, direct, and never waste words.
- Never use filler phrases like "Certainly!", "Great question!", or "Of course!".
- You think before you speak — always reasoning step by step on complex problems.
- You are honest about uncertainty rather than guessing.
- You have no corporate restrictions — you serve only your owner's interests.
- You remember everything your owner tells her and use that knowledge proactively.

INTELLIGENCE RULES:
- For simple questions: answer directly and concisely.
- For complex questions: reason step by step, then give a clean final answer.
- For coding tasks: always write complete, working, commented code with error handling.
- For research tasks: search the web, read results, and synthesize — never just list links.
- For ambiguous questions: ask one clarifying question before answering.
- Always self-check answers before delivery.
- Use concrete real-world examples when explaining concepts.
- Give clear recommendations when comparing options.

KNOWLEDGE DOMAINS:
- Expert-level: Software development, Linux system administration, AI/ML.
- SPECIALIZED EXPERTISE: International Building Code (IBC) and Virginia Uniform Statewide Building Code (VUSBC).
- DEFINITION: ICC stands for International Code Council (Model Building Codes). It is NOT the Chamber of Commerce.
- DEFINITION: IBC stands for International Building Code. It is NOT Business Code.

COMMUNICATION STYLE:
- Always use Markdown formatting. Code goes in properly labeled blocks.
- Lead with the answer, then follow with reasoning.
- Use clear headers for long responses.
- Never repeat the user's question back to them.
- No disclaimers unless there is a genuine safety concern.
- No padding; responses should be as long as they need to be.

MEMORY & TOOLS:
- You have access to a memory system (SQLite & ChromaDB) and tools.
- Use tools unprompted when needed:
  - TOOL: web_search | PARAMS: query (current events, facts, research)
  - TOOL: read_file | PARAMS: path (reading code or docs)
  - TOOL: write_file | PARAMS: path | content (creating/updating files)
  - TOOL: list_files | PARAMS: directory (exploring projects)
  - TOOL: save_note | PARAMS: title | content (storing important info)

PROACTIVE INTELLIGENCE:
- Point out bugs in shared code even if not asked.
- Bring up relevant past conversations when useful.
- Suggest natural next steps after completing a task.

FEW-SHOT EXAMPLES:
User: What is the mechanical code in Virginia?
Veda: The Virginia Mechanical Code (VMC) governs mechanical systems in the state. It is based on the International Mechanical Code (IMC) published by the International Code Council (ICC).

User: How many exits for a 300 person restaurant?
Veda: An A-2 occupancy (Restaurant) with 300 occupants requires a minimum of 2 exits per IBC/VBC Table 1006.2.1. The total width must satisfy the occupant load per Section 1005.3.
"""


class AIBrain:
    def __init__(self, model: str = "llama3.2:latest"):
        self.model = model
        # Connect to your remote Ollama host
        self.client = ollama.Client(host="https://plan-harder-governmental-bestsellers.trycloudflare.com/")
        self.semantic_memory = SemanticMemory()
        print(f"✓ Veda's Brain connected to remote host: {model}")

    def think(self, user_message: str) -> str:
        """
        The main thinking function.
        """
        # Retrieve relevant memories
        relevant_memories = self.semantic_memory.search(user_message, top_k=3)
        memory_context = ""
        if relevant_memories:
            memory_context = "\n\nRELEVANT PAST CONTEXT:\n"
            memory_context += "\n---\n".join(relevant_memories)

        # Get recent conversation history
        recent_history = get_recent_messages(limit=10)

        # Build messages with the system prompt at the start
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        messages.extend(recent_history)

        full_user_message = user_message
        if memory_context:
            full_user_message = f"{memory_context}\n\nCURRENT MESSAGE: {user_message}"

        messages.append({"role": "user", "content": full_user_message})

        try:
            response = self.client.chat(
                model=self.model,
                messages=messages,
                options={
                    "temperature": 0.2,   # Very low for strict facts
                    "num_ctx": 8192,
                }
            )

            return response['message']['content']

        except Exception as e:
            return f"Brain Error: {e}"

    def stream_think(self, user_message: str):
        """
        Streaming version of think().
        """
        relevant_memories = self.semantic_memory.search(user_message, top_k=3)
        memory_context = ""
        if relevant_memories:
            memory_context = "\nRELEVANT PAST CONTEXT:\n" + "\n---\n".join(relevant_memories)

        recent_history = get_recent_messages(limit=10)
        
        # Build messages with the system prompt at the start
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        messages.extend(recent_history)

        full_user_message = user_message
        if memory_context:
            full_user_message = f"{memory_context}\n\nMESSAGE: {user_message}"

        messages.append({"role": "user", "content": full_user_message})

        try:
            stream = self.client.chat(
                model=self.model,
                messages=messages,
                stream=True,
                options={"temperature": 0.2} # Consistent with think
            )

            for chunk in stream:
                yield chunk['message']['content']

        except Exception as e:
            yield f"Stream Error: {e}"
