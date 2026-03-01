# persona/skills/building_code.py
from skills.base import VedaSkill
from typing import List

class BuildingCodeSkill(VedaSkill):
    def name(self) -> str: return "Code Compliance & Research Specialist"
    def description(self) -> str: return "Expert research and interpretation of IBC, VMC, and state-specific building codes."
    def tags(self) -> List[str]: return ["Engineering", "Compliance", "Architecture"]
    def triggers(self) -> List[str]: return ["building code", "ibc", "compliance", "regulation", "vmc", "ipc", "vpc"]

    def knowledge_block(self) -> str:
        return """
        BUILDING CODE REASONING FRAMEWORK:
        1. JURISDICTION: Identify if the requirement is local, state (e.g., Virginia), or national (ICC).
        2. CODE SELECTION: Determine applicable code (VMC for mechanical, VPC for plumbing).
        3. SECTION LOOKUP: Map the query to specific code chapters (e.g., VMC Chapter 4 for Ventilation).
        4. TECHNICAL REQUIREMENT: Extract precise values (CFM, distance, material type).
        5. CITATION: Every answer must cite the specific section (e.g., "Per VMC 401.2...").
        """

    def execute(self, brain, user_message: str) -> str:
        prompt = f"{self.get_context()}
Research this compliance query and provide a cited technical answer:

{user_message}"
        return brain.think(prompt)
