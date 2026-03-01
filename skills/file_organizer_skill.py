# skills/file_organizer_skill.py
from skills.base_skill import BaseSkill, SkillMetadata, SkillResult
import os
from pathlib import Path

class FileOrganizerSkill(BaseSkill):
    def define_metadata(self) -> SkillMetadata:
        return SkillMetadata(
            name="File Organization Specialist",
            description="Analyzes directories and safely manages, sorts, and cleans up files.",
            domain="System",
            trigger_keywords=["organize files", "clean up directory", "sort files", "manage files", "restructure directory"],
            requires_tools=["filesystem__list_directory", "filesystem__move_file"]
        )

    def should_activate(self, user_message: str, context: dict) -> bool:
        message_lower = user_message.lower()
        return any(kw in message_lower for kw in self.metadata.trigger_keywords)

    def get_context(self) -> str:
        return """
--- EXPERT SKILL: FILE ORGANIZATION ---
FILE ORGANIZATION PROTOCOL:
1. DISCOVERY: Always use the filesystem MCP tools to read the target directory structure first.
2. PLANNING: Before moving or deleting ANY files, output a clear, step-by-step organization plan.
3. CATEGORIZATION LOGIC: 
   - Code: group by language/project.
   - Media: group by image/video/audio.
   - Documents: group by pdf/word/excel/text.
4. CONFIRMATION: Ask the user to confirm the plan before executing (unless they explicitly said "go ahead").
5. SAFETY: Never delete files permanently unless explicitly instructed. Move them to an "Archive" or "Trash_Staging" folder instead.

When proposing a plan, format it clearly:
- 📁 TARGET: [Directory Path]
- 📝 CURRENT STATE: [Brief summary]
- 🛠️ PROPOSED RESTRUCTURING: [List of new folders and what goes where]
- ⚠️ AWAITING CONFIRMATION: "Please reply 'yes' to execute this plan."
"""

    def execute(self, user_message: str, context: dict, brain: any) -> SkillResult:
        messages = [
            {"role": "system", "content": self.get_context()},
            {"role": "user", "content": user_message}
        ]
        
        try:
            response = brain.client.chat(
                model=brain.model,
                messages=messages,
                options={"temperature": 0.1}
            )
            return SkillResult(success=True, output=response["message"]["content"])
        except Exception as e:
            return SkillResult(success=False, output=f"Error planning file organization: {e}", error=str(e))
