# veda_agent/skills/manager.py
# VEDA ARCHITECT: PHASE 2 - THE SKILL MANAGER
# Dynamically loads and triggers Skills in the reasoning loop.

import os
import importlib.util
from pathlib import Path
from typing import List, Optional
from .base import VedaSkill

class SkillManager:
    """Discovers, loads, and triggers Veda Skills."""

    def __init__(self, skills_dir: str):
        self.skills_dir = Path(skills_dir)
        self.skills: List[VedaSkill] = []
        self._load_all_skills()

    def _load_all_skills(self):
        """Discovers and imports all .py skills in the directory."""
        if not self.skills_dir.exists():
            self.skills_dir.mkdir(parents=True, exist_ok=True)
            return

        for skill_file in self.skills_dir.glob("*.py"):
            if skill_file.name == "__init__.py":
                continue
            
            # Load module dynamically
            module_name = f"skills.persona.{skill_file.stem}"
            spec = importlib.util.spec_from_file_location(module_name, skill_file)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                # Find classes that inherit from VedaSkill
                for name, obj in module.__dict__.items():
                    if (isinstance(obj, type) and 
                        issubclass(obj, VedaSkill) and 
                        obj is not VedaSkill):
                        self.skills.append(obj())
                        print(f"✓ Skill Loaded: {obj().name()}")

    def detect_skills(self, user_message: str) -> List[VedaSkill]:
        """Returns all skills that should be triggered by the user input."""
        return [skill for skill in self.skills if skill.should_activate(user_message)]

    def get_skill_by_name(self, name: str) -> Optional[VedaSkill]:
        """Finds a specific skill by its formal name."""
        for skill in self.skills:
            if skill.name() == name:
                return skill
        return None

    def list_all_skills(self) -> List[dict]:
        """Returns metadata for all loaded skills."""
        return [skill.metadata for skill in self.skills]
