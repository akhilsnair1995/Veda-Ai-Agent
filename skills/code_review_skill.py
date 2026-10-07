# skills/code_review_skill.py
from skills.base_skill import BaseSkill, SkillMetadata, SkillResult

class CodeReviewSkill(BaseSkill):
    def define_metadata(self) -> SkillMetadata:
        return SkillMetadata(
            name="Code Review & Quality Auditor",
            description="Deep analysis of source code for bugs, security, and architecture.",
            domain="Programming",
            trigger_keywords=["review", "debug", "refactor", "fix code", "improve this code", "check this code"]
        )

    def should_activate(self, user_message: str, context: dict) -> bool:
        message_lower = user_message.lower()
        if any(kw in message_lower for kw in self.metadata.trigger_keywords):
            # Also check if it looks like there's code or a file mention
            if "```" in user_message or "def " in user_message or "class " in user_message or "{" in user_message:
                return True
        return False

    def get_context(self) -> str:
        return """
--- EXPERT SKILL: CODE REVIEW ---
CODE REVIEW PROTOCOL:
1. BUG DETECTION: Logic errors, off-by-one, null pointers, race conditions, type mismatches.
2. SECURITY: Check for OWASP Top 10 (Injection, Broken Auth, XSS, insecure deserialization, etc.).
3. DESIGN: DRY (Don't Repeat Yourself), SOLID principles, YAGNI, loose coupling.
4. PERFORMANCE: Time complexity (Big O), memory leaks, redundant loops, inefficient queries.
5. MODERNITY: Idiomatic use of the language (e.g., list comprehensions in Python, map/reduce in JS).

OUTPUT FORMAT:
Provide your review in the following exact structure:
- 🛑 BUGS: Critical functional errors.
- 🔒 SECURITY: Vulnerabilities and leak risks.
- 📈 IMPROVEMENTS: Readability, performance, and architectural suggestions.
- ✅ CORRECTED VERSION: The final, optimized code block, ready to copy-paste.
"""

    def execute(self, user_message: str, context: dict, brain: any) -> SkillResult:
        # Construct the specialized prompt
        prompt = "Analyze the following code request based on the Code Review Protocol:\n\n" + user_message
        
        messages = [
            {"role": "system", "content": self.get_context()},
            {"role": "user", "content": prompt}
        ]
        
        try:
            response = brain.client.chat.completions.create(
                model=brain.model,
                messages=messages,
                temperature=0.1
            )
            content = response.choices[0].message.content
            return SkillResult(success=True, output=content)
        except Exception as e:
            return SkillResult(success=False, output=f"Error executing Code Review: {e}", error=str(e))

    def validate(self, result: SkillResult) -> bool:
        if not result.success:
            return False
        # A good review must include a corrected code block
        return "```" in result.output and "✅ CORRECTED VERSION:" in result.output
