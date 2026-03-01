# skills/building_code_skill.py
from skills.base_skill import BaseSkill, SkillMetadata, SkillResult

class BuildingCodeSkill(BaseSkill):
    def define_metadata(self) -> SkillMetadata:
        return SkillMetadata(
            name="Universal Engineering Code Specialist",
            description="Expert research and interpretation of global building codes, IBC, IMC, ASHRAE, NFPA, etc.",
            domain="Engineering",
            trigger_keywords=["building code", "ibc", "compliance", "regulation", "imc", "ipc", "nfpa", "ashrae", "engineering standard"]
        )

    def should_activate(self, user_message: str, context: dict) -> bool:
        message_lower = user_message.lower()
        return any(kw in message_lower for kw in self.metadata.trigger_keywords)

    def get_context(self) -> str:
        return """
--- EXPERT SKILL: UNIVERSAL ENGINEERING CODE RESEARCH ---
ENGINEERING CODE REASONING FRAMEWORK:
1. JURISDICTION & AUTHORITY: Identify the AHJ (Authority Having Jurisdiction) and the applicable code edition (e.g., 2021 IBC, ASHRAE 62.1-2019).
2. CODE/STANDARD SELECTION: Determine applicable foundational code or standard (IMC for mechanical, IPC for plumbing, IBC for life safety, NFPA for fire).
3. SECTION LOOKUP: Map the query to specific code chapters and sections (e.g., IMC Chapter 4 for Ventilation).
4. TECHNICAL REQUIREMENT: Extract precise engineering values (CFM, pipe sizing, material type, fire rating).
5. CITATION: Every technical claim MUST cite the exact code or standard section (e.g., "Per 2021 IMC 401.2...").
6. EXCEPTIONS & LOCAL AMENDMENTS: Always state if there are common exceptions or advise the user to verify local amendments.

OUTPUT FORMAT:
- JURISDICTION & APPLICABLE CODE/STANDARD
- RELEVANT SECTION(S)
- EXACT REQUIREMENTS
- PRACTICAL ENGINEERING IMPLICATIONS
"""

    def execute(self, user_message: str, context: dict, brain: any) -> SkillResult:
        prompt = "Using the Building Code Reasoning Framework, answer this compliance query:\n\n" + user_message
        
        try:
            messages = [
                {"role": "system", "content": self.get_context() + "\n\n" + getattr(brain, "VEDA_SYSTEM_PROMPT", "You are Veda.")},
                {"role": "user", "content": prompt}
            ]
            
            response = brain.client.chat(
                model=brain.model,
                messages=messages,
                options={"temperature": 0.1}
            )
            
            return SkillResult(success=True, output=response["message"]["content"])
            
        except Exception as e:
            return SkillResult(success=False, output=f"Error researching building codes: {e}", error=str(e))
