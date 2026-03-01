# persona/skills/self_improvement.py
from skills.base import VedaSkill
from typing import List
import os
from pathlib import Path

class SelfImprovementSkill(VedaSkill):
    def name(self) -> str: return "Veda Self-Evolution Core"
    def description(self) -> str: return "The meta-skill allowing Veda to autonomously generate and install new expert skills based on taught knowledge."
    def tags(self) -> List[str]: return ["Meta", "Evolution", "Code Generation"]
    def triggers(self) -> List[str]: return ["learn a new skill", "add expertise", "create a skill", "crystallize this knowledge", "build a skill for"]

    def knowledge_block(self) -> str:
        return """
        SELF-EVOLUTION PROTOCOL:
        1. KNOWLEDGE ANALYSIS: Extract key technical facts, triggers, and logic from the user's instruction.
        2. CODE GENERATION: Draft a new Python file inheriting from 'VedaSkill'.
        3. FILE INTEGRATION: Save the file to 'persona/skills/'.
        4. REGISTRY RELOAD: Instruct the user to restart Veda or use '/skills' to refresh the manager.
        5. VALIDATION: Perform a dry run of the new skill logic.
        """

    def execute(self, brain, user_message: str) -> str:
        # Veda must output the exact TOOL: write_file call to create the skill
        prompt = f"{self.get_context()}

USER REQUEST: {user_message}

Draft the complete Python skill file based on our interaction."
        return brain.think(prompt)
