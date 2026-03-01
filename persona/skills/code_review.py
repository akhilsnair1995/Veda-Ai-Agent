# persona/skills/code_review.py
from skills.base import VedaSkill
from typing import List, Dict

class CodeReviewSkill(VedaSkill):
    def name(self) -> str: return "Code Quality & Security Auditor"
    def description(self) -> str: return "Deep analysis of source code for bugs, security vulnerabilities, and architectural improvements."
    def tags(self) -> List[str]: return ["Programming", "Security", "Clean Code"]
    def triggers(self) -> List[str]: return ["review", "debug", "refactor", "fix code", "improve this"]

    def knowledge_block(self) -> str:
        return """
        CODE REVIEW PROTOCOL:
        1. BUG DETECTION: Logic errors, off-by-one, null pointers, race conditions.
        2. SECURITY: Check for OWASP Top 10 (Injection, Broken Auth, XSS, etc.).
        3. DESIGN: DRY (Don't Repeat Yourself), SOLID principles, YAGNI.
        4. PERFORMANCE: Time complexity (Big O), memory leaks, redundant loops.
        
        OUTPUT FORMAT:
        - 🛑 BUGS: Critical functional errors.
        - 🔒 SECURITY: Vulnerabilities and leak risks.
        - 📈 IMPROVEMENTS: Readability and performance suggestions.
        - ✅ CORRECTED VERSION: The final, optimized code block.
        """

    def execute(self, brain, user_message: str) -> str:
        prompt = f"{self.get_context()}
Analyze this code following the protocol:

{user_message}"
        return brain.think(prompt)
