# veda_agent/skills/base.py
# VEDA ARCHITECT: PHASE 1 - THE SKILL FOUNDATION
# This is the base class for all Veda expert-level capabilities.

import abc
from typing import List, Dict, Any, Optional

class VedaSkill(abc.ABC):
    """
    A Veda Skill is a modular, high-fidelity expertise.
    It combines metadata, context injection, and agentic execution.
    """

    def __init__(self):
        # 1. METADATA: Identifying the expertise
        self.metadata = {
            "name": self.name(),
            "description": self.description(),
            "version": "1.0.0",
            "domain_tags": self.tags(),
            "trigger_keywords": self.triggers()
        }

    @abc.abstractmethod
    def name(self) -> str:
        """The formal name of the skill."""
        pass

    @abc.abstractmethod
    def description(self) -> str:
        """What this skill performs for Veda's owner."""
        pass

    @abc.abstractmethod
    def tags(self) -> List[str]:
        """Domain tags (e.g., ['Engineering', 'HVAC'])."""
        pass

    @abc.abstractmethod
    def triggers(self) -> List[str]:
        """Keywords that should activate this skill."""
        pass

    # 2. TRIGGER DETECTOR: Should this skill activate?
    def should_activate(self, user_message: str) -> bool:
        """
        Determines if the skill is relevant to the user's input.
        By default, it checks trigger keywords.
        """
        message_lower = user_message.lower()
        return any(keyword.lower() in message_lower for keyword in self.triggers())

    # 3. CONTEXT INJECTOR: Load knowledge into the brain
    def get_context(self) -> str:
        """
        Returns a block of expert knowledge/logic to be 
        injected into Veda's system prompt.
        """
        return f"
--- EXPERT SKILL ACTIVATED: {self.name()} ---
{self.knowledge_block()}
"

    @abc.abstractmethod
    def knowledge_block(self) -> str:
        """The actual expert reference material for the LLM."""
        pass

    # 4. EXECUTOR: Perform the agentic work
    def execute(self, brain: Any, user_message: str) -> str:
        """
        The main reasoning and action loop for this specific skill.
        Can be overridden for complex multi-step workflows.
        """
        # Inject context and get response from brain
        prompt = f"{self.get_context()}

USER REQUEST: {user_message}"
        return brain.think(prompt)

    # 5. VALIDATOR: Quality control
    def validate(self, output: str) -> bool:
        """Check if the output meets the skill's technical standards."""
        return True

    # 6. EXAMPLES: For few-shot reasoning
    def examples(self) -> List[Dict[str, str]]:
        """A list of sample inputs and expected outputs."""
        return []
