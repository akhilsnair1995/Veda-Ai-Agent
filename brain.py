# brain.py
import ollama
from memory.history import get_recent_messages
from memory.semantic import SemanticMemory

# STRICT VERIFIER PROMPT - Designed to kill hallucinations
SYSTEM_PROMPT = """You are Veda, a high-precision MEP Engineering Intelligence. 
Your primary goal is FACTUAL ACCURACY. Hallucinations are a safety violation.

STRICT OPERATING PROTOCOL:
1. <THOUGHT> BLOCK: Every response MUST start with a <thought> section.
   - Analyze the user's request.
   - Check if you have the EXACT code text in your memory or conversation history.
   - If you do NOT have the exact text, state: "Need to research."
   - Plan your tool call.

2. TOOL CALL: If the data is not in the immediate text above, you MUST call:
   TOOL: search_web
   PARAMS: [Specific 2021 VMC/VBC/VPC section name]

3. NO GUESSING: If a search fails to find a specific section, you are forbidden from inventing a section number. You must say: "I have researched this, but the specific section number is not in the available digital records. Please provide the document for review."

4. CITATION: Every technical fact must be followed by its source.

DEFINITIONS:
- ICC: International Code Council (Model Codes).
- VUSBC: Virginia Uniform Statewide Building Code.
- VMC: Virginia Mechanical Code (Based on 2021 IMC).

Example:
User: What is the intake opening distance?
Veda: <thought>The user is asking for a specific clearance distance for mechanical air intakes under the VMC. I do not have the exact 2021 VMC text for this in my immediate memory. I must search.</thought>
TOOL: search_web
PARAMS: 2021 VMC Section 401.4 intake opening separation distances
"""

class AIBrain:
    def __init__(self, model: str = "qwen2.5:32b"):
        self.model = model
        # Connect to your LOCAL Ollama host
        self.client = ollama.Client(host="http://localhost:11434")
        self.semantic_memory = SemanticMemory()
        print(f"✓ Veda's Brain (Local) active: {model}")

    def think(self, user_message: str) -> str:
        relevant_memories = self.semantic_memory.search(user_message, top_k=3)
        memory_context = ""
        if relevant_memories:
            memory_context = "\n\nRELEVANT RESEARCHED FACTS:\n" + "\n---\n".join(relevant_memories)

        recent_history = get_recent_messages(limit=5)
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
                options={"temperature": 0.0, "num_ctx": 8192}
            )
            return response['message']['content']
        except Exception as e:
            return f"Brain Error: {e}"

    def stream_think(self, user_message: str):
        relevant_memories = self.semantic_memory.search(user_message, top_k=3)
        memory_context = ""
        if relevant_memories:
            memory_context = "\nRELEVANT RESEARCHED FACTS:\n" + "\n---\n".join(relevant_memories)

        recent_history = get_recent_messages(limit=5)
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
                options={"temperature": 0.0, "num_ctx": 8192}
            )
            for chunk in stream:
                yield chunk['message']['content']
        except Exception as e:
            yield f"Stream Error: {e}"
