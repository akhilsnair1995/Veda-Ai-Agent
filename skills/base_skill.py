# skills/base_skill.py
# The foundation class every Veda skill must inherit from.
# Think of this as the DNA of every skill Veda will ever have.

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any
import json


@dataclass
class SkillMetadata:
    name: str
    description: str
    version: str = "1.0.0"
    author: str = "Veda"
    created: str = field(default_factory=lambda: datetime.now().isoformat())
    domain: str = "general"
    trigger_keywords: list[str] = field(default_factory=list)
    requires_tools: list[str] = field(default_factory=list)
    requires_memory: bool = False
    requires_web: bool = False


@dataclass  
class SkillResult:
    success: bool
    output: str
    metadata: dict = field(default_factory=dict)
    error: str = None
    sources: list[str] = field(default_factory=list)
    confidence: float = 1.0


class BaseSkill(ABC):
    """
    Every skill Veda has must inherit from this class.
    
    A skill is a specialized capability that Veda activates
    when she detects a relevant task. It brings its own:
    - Knowledge context (what to know before attempting)
    - Trigger logic (when to activate)
    - Execution logic (how to perform the task)
    - Validation logic (how to verify quality)
    """

    def __init__(self):
        self.metadata = self.define_metadata()
        self._knowledge_cache = None

    @abstractmethod
    def define_metadata(self) -> SkillMetadata:
        """Define this skill's identity and capabilities."""
        pass

    @abstractmethod
    def should_activate(self, user_message: str, context: dict) -> bool:
        """
        Return True if this skill should handle the given message.
        This is called for every user message — keep it fast.
        """
        pass

    @abstractmethod
    def get_context(self) -> str:
        """
        Return the knowledge and instructions this skill
        needs injected into the prompt before executing.
        This is how skills carry their expertise.
        """
        pass

    @abstractmethod
    def execute(self, user_message: str, 
                context: dict, 
                brain: Any) -> SkillResult:
        """
        Perform the skill's main work.
        Has access to user message, context dict, and Veda's brain.
        Must return a SkillResult.
        """
        pass

    def validate(self, result: SkillResult) -> bool:
        """
        Check if the skill's output meets quality standards.
        Override this in subclasses for domain-specific validation.
        Default: just check it's not empty.
        """
        return bool(result.output and len(result.output) > 10)

    def to_dict(self) -> dict:
        """Serialize skill metadata for the registry."""
        return {
            "name": self.metadata.name,
            "description": self.metadata.description,
            "version": self.metadata.version,
            "domain": self.metadata.domain,
            "trigger_keywords": self.metadata.trigger_keywords,
            "requires_tools": self.metadata.requires_tools,
        }

    def __repr__(self):
        return f"Skill({self.metadata.name} v{self.metadata.version})"
