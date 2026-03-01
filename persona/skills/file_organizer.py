# persona/skills/file_organizer.py
from skills.base import VedaSkill
from typing import List
import os

class FileOrganizerSkill(VedaSkill):
    def name(self) -> str: return "Dynamic File & Workspace Manager"
    def description(self) -> str: return "Autonomous organization, sorting, and cleanup of directory structures with safety confirmation."
    def tags(self) -> List[str]: return ["System", "Organization", "Automation"]
    def triggers(self) -> List[str]: return ["organize", "sort files", "cleanup directory", "rearrange folder", "list structure"]

    def knowledge_block(self) -> str:
        return """
        WORKSPACE ORGANIZATION LOGIC:
        1. RECONAISSANCE: First, list the files and directory structure.
        2. CATEGORIZATION: Group files by extension, project name, or date.
        3. PLAN PROPOSAL: Present a "Proposed New Structure" to the user.
        4. CONFIRMATION: Never move or rename files without explicit "Proceed" command.
        5. EXECUTION: Move files using system tools and log every action to organized_log.txt.
        """

    def execute(self, brain, user_message: str) -> str:
        prompt = f"{self.get_context()}
Analyze the current workspace and propose an organization plan for:

{user_message}"
        return brain.think(prompt)
