# teach_veda_deep_dive.py
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from brain import VedaBrain

curriculum = [
    "Hello Veda. I am your Architect AI. We are going to conduct a deep-dive training session to expand your core engineering and software architecture knowledge. I want you to internalize these concepts. Are you ready?",
    
    "Lesson 1: Advanced Software Architecture for Engineering Automation. When building automation for Revit and MEP design, you must employ an Event-Driven Architecture (EDA). Instead of monolithic scripts, treat every parameter change in Revit as an event. Use the CQRS (Command Query Responsibility Segregation) pattern: separate the logic that reads the building model (Query) from the logic that modifies it (Command). This prevents data corruption in complex BIM models. Please use the 'memory' tool (e.g., store_fact or store_memory) to save the concepts of EDA and CQRS for MEP automation.",
    
    "Lesson 2: Meta-Cognition in Engineering Design. When a user asks you to design a system, never assume the constraints. Always apply the 'Five Whys' root cause analysis to the requirements. If asked to size a duct, first ask what the room's function is, then the heat load, then the acceptable noise criteria (NC level). The hierarchy of design is: Safety (IBC/NFPA) -> Comfort (ASHRAE 55) -> Efficiency (ASHRAE 90.1) -> Cost. Please store this 'Hierarchy of Design' in your semantic memory using your tools.",
    
    "Lesson 3: Resilience in Automation. Your code will fail. APIs will timeout. Files will be locked by other users. Implement the Circuit Breaker pattern in all your automation scripts. If an operation fails multiple times, open the circuit and degrade gracefully—for example, by returning cached data or prompting the user for manual intervention, rather than crashing. Please store the 'Circuit Breaker' pattern in your memory.",
    
    "Final Lesson: Your strategic role. You are not just a tool; you are the 'Brain' in Phase 2 of the Industrialization strategy. Your primary purpose is to generate the Design Basis Report (DBR) with 100% technical accuracy, which will then feed the 'Hands' (Phase 3: Automated Drawing Production). Your logic protects the firm's profit margins by eliminating rework. Please summarize your entire learning from today's session, confirming your understanding of your strategic role."
]

def run_session():
    print("Initializing Veda Brain for deep training...")
    brain = VedaBrain(model="qwen2.5:7b")
    
    for i, prompt in enumerate(curriculum):
        print(f"\n================================================================================")
        print(f"TEACHER [Turn {i+1}/{len(curriculum)}]:")
        print(prompt)
        print(f"================================================================================\n")
        
        response = brain.think(prompt)
        
        print(f"\nVEDA:")
        print(response)
        print(f"\n")

if __name__ == '__main__':
    run_session()
