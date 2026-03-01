# skills/building_code_skill.py
from skills.base_skill import BaseSkill, SkillMetadata, SkillResult

class BuildingCodeSkill(BaseSkill):
    def define_metadata(self) -> SkillMetadata:
        return SkillMetadata(
            name="Building Code Research Specialist",
            description="Expert research and interpretation of IBC, VMC, and state-specific codes.",
            domain="Engineering",
            trigger_keywords=["building code", "ibc", "compliance", "regulation", "vmc", "ipc", "vpc", "nfpa", "ashrae"]
        )

    def should_activate(self, user_message: str, context: dict) -> bool:
        message_lower = user_message.lower()
        return any(kw in message_lower for kw in self.metadata.trigger_keywords)

    def get_context(self) -> str:
        return """
--- EXPERT SKILL: BUILDING CODE RESEARCH ---
BUILDING CODE REASONING FRAMEWORK:
1. JURISDICTION: Identify if the requirement is local, state (e.g., Virginia VUSBC), or national (ICC).
2. CODE SELECTION: Determine applicable code (VMC for mechanical, VPC for plumbing, IBC for structural/life safety).
3. SECTION LOOKUP: Map the query to specific code chapters (e.g., VMC Chapter 4 for Ventilation, Chapter 6 for Duct Systems).
4. TECHNICAL REQUIREMENT: Extract precise values (CFM, distance, material type, fire rating).
5. CITATION: Every technical claim MUST cite the specific section (e.g., "Per VMC 401.2...").
6. EXCEPTIONS: Always state if there are common exceptions to the primary rule.

OUTPUT FORMAT:
- JURISDICTION & APPLICABLE CODE
- RELEVANT SECTION(S)
- EXACT REQUIREMENTS
- PRACTICAL ENGINEERING IMPLICATIONS
"""

    def execute(self, user_message: str, context: dict, brain: any) -> SkillResult:
        # Try to use MCP Notes server or semantic memory for specific local codes if available
        # We will embed the search command directly to the brain's main process which handles tools
        
        prompt = f"Using the Building Code Reasoning Framework, answer this compliance query:

{user_message}"
        
        try:
            # We call the brain to process this so it can use MCP tools (like web search or notes)
            # if it needs to look up the code. We wrap it in a system instruction.
            messages = [
                {"role": "system", "content": brain.client.chat(model=brain.model, messages=[{"role": "system", "content": "You are a routing agent."}])['message']['content']}, # Placeholder to satisfy structure
                # Actually, let's just use the brain's existing client directly with our context injected
            ]
            
            messages = [
                {"role": "system", "content": self.get_context() + "

" + getattr(brain, "VEDA_SYSTEM_PROMPT", "You are Veda.")},
                {"role": "user", "content": prompt}
            ]
            
            response = brain.client.chat(
                model=brain.model,
                messages=messages,
                options={"temperature": 0.1}
            )
            
            # Since brain.process() already handles tools, ideally we'd let the brain do it, 
            # but skill execution is internal. Let's return the raw response, and if it has tool calls,
            # brain.process will catch them.
            return SkillResult(success=True, output=response["message"]["content"])
            
        except Exception as e:
            return SkillResult(success=False, output=f"Error researching building codes: {e}", error=str(e))
