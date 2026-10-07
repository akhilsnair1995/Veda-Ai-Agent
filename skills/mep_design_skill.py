# skills/mep_design_skill.py
# Expert MEP Engineering Design Automation Skill for Veda

from skills.base_skill import BaseSkill, SkillMetadata, SkillResult

class MEPDesignSkill(BaseSkill):
    def define_metadata(self) -> SkillMetadata:
        return SkillMetadata(
            name="MEP Engineering Design Specialist",
            description="Automates complex MEP calculations, HVAC load studies, duct & pipe sizing, ventilation rates, and engineering compliance.",
            domain="Engineering",
            trigger_keywords=[
                "mep", "hvac", "duct", "ductwork", "riser", "airflow", "cfm",
                "ventilation", "static pressure", "load calculation", "chiller",
                "psychrometric", "sensible load", "latent load", "pipe friction",
                "ashrae", "imc", "vmc", "exhaust fan", "subduct"
            ]
        )

    def should_activate(self, user_message: str, context: dict) -> bool:
        message_lower = user_message.lower()
        return any(kw in message_lower for kw in self.metadata.trigger_keywords)

    def get_context(self) -> str:
        return """
--- EXPERT SKILL: MEP ENGINEERING DESIGN SPECIALIST ---
STRATEGIC MEP REASONING FRAMEWORK:
1. FIRST PRINCIPLES FIRST:
   - Sensible Heat: Q_s = 1.08 * CFM * delta_T (at standard air density).
   - Total Heat: Q_t = 4.5 * CFM * delta_h (enthalpy change).
   - Airflow & Velocity: CFM = Velocity (FPM) * Area (sq ft).
   - Duct Friction / Sizing: Equal Friction Method (typically 0.08 to 0.10 in. w.g. per 100 ft).
   - High velocity limits for noise: Main risers < 1500-1800 FPM (commercial) or < 1000-1200 FPM (residential).
2. MULTI-STORY RISER & SHAFT DYNAMICS:
   - Exhaust subducting / riser entry: Continuous subduct (e.g. 22" vertical rise per IMC/NFPA) prevents backdraft and fire spread.
   - Shaft free area reduction: Each floor penetration/subduct entering a common riser restricts the gross cross-sectional area.
   - Velocity increase & static pressure: Reduction in net free area increases air velocity -> drastically increases friction losses (proportional to velocity squared) and raises system static pressure on fans upstream/downstream.
3. STANDARDS & CODE COMPLIANCE:
   - Outdoor Air / Ventilation: IMC 403 / ASHRAE 62.1 (cfm/person + cfm/sq ft).
   - Duct Construction: SMACNA standards for gauge, joints, and static pressure classes.
   - Pipe Sizing & Pressure Drop: Hazen-Williams or Darcy-Weisbach formulas; velocity limits 4-10 FPS depending on service.

OUTPUT STRUCTURE:
- ENGINEERING ASSESSMENT: Clear diagnosis and technical evaluation.
- FIRST-PRINCIPLES CALCULATIONS: Formulas, input parameters, and exact numeric outcomes.
- CODE / STANDARD CITATIONS: Applicable sections (IMC, ASHRAE, SMACNA, etc.).
- PRACTICAL RECOMMENDATIONS: Actionable engineering mitigations or sizing adjustments.
"""

    def execute(self, user_message: str, context: dict, brain: any) -> SkillResult:
        prompt = "Using the MEP Engineering Design Framework, analyze and solve this engineering challenge:\n\n" + user_message
        try:
            messages = [
                {"role": "system", "content": self.get_context() + "\n\n" + getattr(brain, "system_prompt", "You are Veda.")},
                {"role": "user", "content": prompt}
            ]
            response = brain.client.chat.completions.create(
                model=brain.model,
                messages=messages,
                temperature=0.1
            )
            return SkillResult(success=True, output=response.choices[0].message.content)
        except Exception as e:
            return SkillResult(success=False, output=f"Error executing MEP design skill: {e}", error=str(e))
