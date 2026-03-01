# veda_agent/persona/skills/mep_design.py
# VEDA ARCHITECT: PHASE 4 - BOOTSTRAP EXPERT SKILL
# Expert MEP Engineering Design Automation.

from skills.base import VedaSkill
from typing import List, Dict

class MEPDesignSkill(VedaSkill):
    """
    Expert MEP Design Skill for Veda.
    Provides deep technical logic for HVAC, Plumbing, and Electrical systems.
    """

    def name(self) -> str:
        return "MEP Engineering Design Specialist"

    def description(self) -> str:
        return "Automates complex MEP calculations, code compliance audits, and system design logic."

    def tags(self) -> List[str]:
        return ["Engineering", "MEP", "HVAC", "Compliance"]

    def triggers(self) -> List[str]:
        return ["design", "hvac", "ventilation", "calculate load", "compliance", "vmc"]

    def knowledge_block(self) -> str:
        return """
        STRATEGIC MEP LOGIC:
        1. LOAD CALCULATION: Always prioritize Sensible vs Latent loads. Use psychrometric first principles.
        2. VENTILATION: Check VMC 403.3 (Outdoor Air Requirements). Verify occupancy rates.
        3. DUCT DESIGN: Equal friction method. Maintain 0.1 in. w.g. per 100 ft.
        4. ELECTRICAL: KVL/KCL for distribution. Standard voltage drops < 3%.
        5. PLUMBING: Fixture units calculation. IPC/VPC compliance required.
        """

    def examples(self) -> List[Dict[str, str]]:
        return [
            {
                "input": "Calculate the ventilation required for a 1000 sq ft office.",
                "output": "Based on VMC 403.3 Table, Office Space requires 5 cfm/person + 0.06 cfm/sq ft. For 1000 sq ft (assuming 15 people), that is 75 + 60 = 135 CFM of outdoor air."
            }
        ]
