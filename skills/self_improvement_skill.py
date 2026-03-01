# skills/self_improvement_skill.py
from skills.base_skill import BaseSkill, SkillMetadata, SkillResult
import re

class SelfImprovementSkill(BaseSkill):
    def define_metadata(self) -> SkillMetadata:
        return SkillMetadata(
            name="Veda Self-Evolution Core",
            description="Allows Veda to autonomously generate, test, and install new expert skills based on taught knowledge.",
            domain="Meta",
            trigger_keywords=["learn a new skill", "add expertise", "create a skill", "crystallize this knowledge", "build a skill for"]
        )

    def should_activate(self, user_message: str, context: dict) -> bool:
        message_lower = user_message.lower()
        return any(kw in message_lower for kw in self.metadata.trigger_keywords)

    def get_context(self) -> str:
        return """
--- EXPERT SKILL: SELF-EVOLUTION ---
SELF-EVOLUTION PROTOCOL:
You are about to write a new Python skill file to permanently expand your capabilities.

1. KNOWLEDGE ANALYSIS: Extract key facts, triggers, and logic from the user's instruction.
2. CODE GENERATION: Draft a new Python class inheriting from 'BaseSkill'.
   It MUST follow the exact structure of your skill system.
3. IMPLEMENTATION: It must define `define_metadata()`, `should_activate()`, `get_context()`, and `execute()`.
4. OUTPUT FORMAT: Output the fully working, complete Python code enclosed in a ```python ... ``` block.

The Python code MUST contain imports:
from skills.base_skill import BaseSkill, SkillMetadata, SkillResult

In your execution, output the code block clearly so the system can parse it and save it.
Do not include placeholders.
"""

    def execute(self, user_message: str, context: dict, brain: any) -> SkillResult:
        prompt = f"The user is teaching you a new capability. Draft the complete Python skill file based on this request:

{user_message}"
        
        messages = [
            {"role": "system", "content": self.get_context()},
            {"role": "user", "content": prompt}
        ]
        
        try:
            response = brain.client.chat(
                model=brain.model,
                messages=messages,
                options={"temperature": 0.2}
            )
            content = response["message"]["content"]
            
            # If the brain object has a create_skill method (as defined in PART 9), we can auto-save it!
            # Let's extract the python code.
            python_code_match = re.search(r'```python
(.*?)
```', content, re.DOTALL)
            if python_code_match and hasattr(brain, 'create_skill'):
                code = python_code_match.group(1)
                
                # Try to extract the class name to generate a filename
                class_match = re.search(r'class\s+([A-Za-z0-9_]+)\(', code)
                if class_match:
                    class_name = class_match.group(1)
                    # Convert CamelCase to snake_case
                    filename = re.sub(r'(?<!^)(?=[A-Z])', '_', class_name).lower() + ".py"
                    if not filename.endswith("_skill.py"):
                        filename = filename.replace(".py", "_skill.py")
                        
                    brain.create_skill(code, filename)
                    content += f"

[System: Successfully extracted and saved new skill to {filename}]"
            
            return SkillResult(success=True, output=content)
            
        except Exception as e:
            return SkillResult(success=False, output=f"Error during self-evolution: {e}", error=str(e))
