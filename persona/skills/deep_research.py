# persona/skills/deep_research.py
from skills.base import VedaSkill
from typing import List

class DeepResearchSkill(VedaSkill):
    def name(self) -> str: return "Synthesized Research Engine"
    def description(self) -> str: return "Comprehensive multi-source research and synthesis on complex topics."
    def tags(self) -> List[str]: return ["Research", "Synthesis", "Investigation"]
    def triggers(self) -> List[str]: return ["deep dive", "research", "investigate", "comprehensive report", "what is the consensus"]

    def knowledge_block(self) -> str:
        return """
        RESEARCH SYNTHESIS PROTOCOL:
        1. MULTI-SOURCE GATHERING: Call search_web multiple times for different perspectives.
        2. TRIANGULATION: Identify points where sources agree (Consensus).
        3. DISPUTE DETECTION: Explicitly flag where sources conflict.
        4. STRUCTURED REPORT:
           - Executive Summary
           - Foundational Facts
           - Consensus Findings
           - Conflicting Viewpoints
           - Citations/Sources
        """

    def execute(self, brain, user_message: str) -> str:
        # This skill triggers a specialized tool cycle in the reasoning loop
        prompt = f"{self.get_context()}
Perform a deep research cycle on this topic:

{user_message}"
        return brain.think(prompt)
