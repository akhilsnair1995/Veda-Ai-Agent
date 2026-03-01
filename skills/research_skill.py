# skills/research_skill.py
from skills.base_skill import BaseSkill, SkillMetadata, SkillResult

class DeepResearchSkill(BaseSkill):
    def define_metadata(self) -> SkillMetadata:
        return SkillMetadata(
            name="Deep Research Specialist",
            description="Comprehensive research on any topic using web search and synthesis.",
            domain="Research",
            trigger_keywords=["research", "deep dive", "investigate", "find out everything about", "comprehensive overview"],
            requires_web=True
        )

    def should_activate(self, user_message: str, context: dict) -> bool:
        message_lower = user_message.lower()
        # Ensure it's a substantive request for research, not just a casual mention
        has_trigger = any(kw in message_lower for kw in self.metadata.trigger_keywords)
        is_long_enough = len(user_message.split()) > 4
        return has_trigger and is_long_enough

    def get_context(self) -> str:
        return """
--- EXPERT SKILL: DEEP RESEARCH ---
DEEP RESEARCH PROTOCOL:
1. GATHER: You MUST use the `web` MCP server (TOOL: web__search) to gather multiple sources of information.
2. SYNTHESIZE: Cross-reference facts across sources.
3. OBJECTIVITY: Identify consensus vs. disputed claims.
4. CITATION: Cite sources using [URL] or [Source Name] inline.
5. STRUCTURE: Organize the final report logically.

REPORT STRUCTURE:
- 📌 EXECUTIVE SUMMARY
- 🔍 KEY FINDINGS (Bullet points with citations)
- ⚖️ CONSENSUS & DISPUTES (What is agreed upon, what is debated)
- 📚 SOURCES CONSULTED

IMPORTANT: Never present a single source's claim as established fact without corroboration.
"""

    def execute(self, user_message: str, context: dict, brain: any) -> SkillResult:
        prompt = "Conduct deep research on the following topic and provide a structured report. You must use the web search tool to gather current information.\n\nTopic: " + user_message
        
        # We return the prompt directly to the brain via the LLM, 
        # so the brain handles the TOOL calls.
        messages = [
            {"role": "system", "content": self.get_context() + "\n\n" + "If you need data, output TOOL: web__search | PARAMS: {\"query\": \"...\"}"},
            {"role": "user", "content": prompt}
        ]
        
        try:
            response = brain.client.chat(
                model=brain.model,
                messages=messages,
                options={"temperature": 0.2}
            )
            return SkillResult(success=True, output=response["message"]["content"])
        except Exception as e:
            return SkillResult(success=False, output=f"Error during deep research: {e}", error=str(e))
