# skills/skill_registry.py
# The brain's skill router. 
# Loads all skills, detects which one to use, and executes it.

import importlib
import inspect
import sys
from pathlib import Path
from typing import Optional
from rich.console import Console
from skills.base_skill import BaseSkill, SkillResult

console = Console()
BASE_DIR = Path(__file__).resolve().parent.parent
SKILLS_DIR = BASE_DIR / "skills"

# Ensure BASE_DIR is in sys.path so dynamic imports work
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))


class SkillRegistry:
    """
    Manages all of Veda's skills.
    
    On startup, scans the skills directory and loads every skill.
    On each user message, checks which skill should activate.
    Routes execution to the right skill automatically.
    """

    def __init__(self):
        self.skills: dict[str, BaseSkill] = {}
        self._load_all_skills()

    def _load_all_skills(self):
        """
        Auto-discover and load all skill files from skills/
        Any file ending in _skill.py is treated as a skill.
        """
        if not SKILLS_DIR.exists():
            SKILLS_DIR.mkdir(parents=True, exist_ok=True)
            
        skill_files = SKILLS_DIR.glob("*_skill.py")
        loaded = 0

        for skill_file in skill_files:
            if skill_file.name == "base_skill.py":
                continue
                
            try:
                # Import the module dynamically
                module_name = f"skills.{skill_file.stem}"
                
                if module_name in sys.modules:
                    importlib.reload(sys.modules[module_name])
                module = importlib.import_module(module_name)

                # Find the skill class (inherits from BaseSkill)
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    if (issubclass(obj, BaseSkill) 
                            and obj is not BaseSkill):
                        skill_instance = obj()
                        self.skills[skill_instance.metadata.name] = skill_instance
                        loaded += 1
                        console.print(
                            f"[dim]✓ Skill loaded: "
                            f"{skill_instance.metadata.name}[/dim]"
                        )

            except Exception as e:
                console.print(
                    f"[yellow]⚠ Could not load skill "
                    f"{skill_file.name}: {e}[/yellow]"
                )

        console.print(
            f"[green]✓ {loaded} skills active[/green]"
        )

    def detect_skill(self, 
                     user_message: str, 
                     context: dict) -> Optional[BaseSkill]:
        """
        Check every loaded skill to see if it should handle 
        this message. Returns the first matching skill, or None.
        """
        for skill in self.skills.values():
            try:
                if skill.should_activate(user_message, context):
                    return skill
            except Exception:
                pass
        return None

    def execute_skill(self, 
                      skill: BaseSkill,
                      user_message: str,
                      context: dict,
                      brain: any) -> SkillResult:
        """
        Execute a skill and validate its output.
        If validation fails, retry once with a correction prompt.
        """
        console.print(
            f"[cyan]⚡ Skill activated: "
            f"{skill.metadata.name}[/cyan]"
        )

        result = skill.execute(user_message, context, brain)

        if not skill.validate(result):
            console.print(
                f"[yellow]⚠ Skill output failed validation. "
                f"Retrying...[/yellow]"
            )
            # Retry with explicit quality instruction
            retry_message = (
                f"Your previous response was incomplete or incorrect. "
                f"Try again more carefully. Original request: {user_message}"
            )
            result = skill.execute(retry_message, context, brain)

        return result

    def list_skills(self) -> list[dict]:
        """Return a summary of all loaded skills."""
        return [s.to_dict() for s in self.skills.values()]

    def get_skill(self, name: str) -> Optional[BaseSkill]:
        """Get a skill by name."""
        return self.skills.get(name)

    def reload_skills(self):
        """Reload all skills from disk. Useful after creating new ones."""
        self.skills.clear()
        self._load_all_skills()
