# trainer.py
# Specialized script for Teacher AI to interact with and train Veda.

import sys
from brain import VedaBrain
from memory.semantic import SemanticMemory

def train_veda(question, expected_key_points, teacher_feedback_template):
    brain = VedaBrain()
    semantic_memory = SemanticMemory()
    
    print(f"\n[TEACHER] Testing Veda with: {question}")
    
    # 1. Get Veda's response
    response = brain.think(question)
    print(f"\n[VEDA RESPONSE]:\n{response}")
    
    # 2. Evaluate (Simulated evaluation logic)
    missing_points = [p for p in expected_key_points if p.lower() not in response.lower()]
    
    if not missing_points:
        feedback = f"PERFECT. Veda correctly identified: {', '.join(expected_key_points)}."
        print(f"\n[TEACHER EVALUATION]: {feedback}")
    else:
        # 3. Create a correction and store it in her semantic memory
        correction = teacher_feedback_template.format(response=response, missing=", ".join(missing_points))
        print(f"\n[TEACHER CORRECTION]: {correction}")
        
        # We store the correction as a "System/Teacher Correction" in her semantic memory
        # Veda's prompt tells her to prioritize RELEVANT PAST CONTEXT
        semantic_memory.store(
            text=f"TEACHER CORRECTION on '{question}': {correction}",
            metadata={"type": "teacher_correction", "topic": "IBC/VMC"}
        )
        print("\n[SYSTEM] Correction stored in Veda's long-term semantic memory.")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Can be used for custom training
        pass
    else:
        # Run a standardized training module
        train_veda(
            question="What code governs mechanical systems in Virginia, and what is its base model code?",
            expected_key_points=["VMC", "Virginia Mechanical Code", "IMC", "International Mechanical Code"],
            teacher_feedback_template="Veda, your response was: '{response}'. You missed mentioning: {missing}. Remember: In Virginia, the IMC is adopted as the VMC (Virginia Mechanical Code)."
        )
