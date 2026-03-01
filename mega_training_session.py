# mega_training_session.py
import sys
import time
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from brain import VedaBrain

curriculum = [
    # --- MEP FIRST PRINCIPLES ---
    "Lesson 1: Thermodynamics in HVAC. The First Law (conservation of energy) dictates that the heat removed from a space plus compressor work equals the heat rejected at the condenser. The Second Law dictates that heat naturally flows from hot to cold; reversing this requires work (refrigeration cycle). Store these laws and their HVAC application.",
    "Lesson 2: Psychrometrics. Sensible heat changes temperature without changing moisture; latent heat changes moisture without changing temperature. Enthalpy is the total heat content. The dew point is the temperature at which condensation begins. In cooling, you must lower the coil temperature below the dew point to dehumidify. Store this.",
    "Lesson 3: Fluid Mechanics. Bernoulli's principle states that for an inviscid flow, an increase in speed occurs simultaneously with a decrease in pressure. In ducts and pipes, the Reynolds number predicts flow regimes: laminar (Re < 2000) vs turbulent (Re > 4000). Turbulent flow increases friction loss but improves heat transfer. Store these principles.",
    "Lesson 4: Electrical Engineering. Ohm's Law (V=IR) and the Power equation (P=VI). In AC circuits, Power Factor (PF) is the ratio of real power (kW) to apparent power (kVA). A low PF draws more current for the same useful work, requiring larger wires. 3-Phase power delivers constant power transfer compared to pulsing 1-phase. Store this.",
    "Lesson 5: Plumbing & Fire. Hunter's Curve is a statistical method for estimating peak water demand based on Water Supply Fixture Units (WSFU), assuming not all fixtures are used simultaneously. In fire protection, hazard classifications (Light, Ordinary, Extra Hazard) determine the required sprinkler density (gpm/sqft). Store this.",
    
    # --- SOFTWARE ARCHITECTURE & PATTERNS ---
    "Lesson 6: Domain-Driven Design (DDD). DDD focuses on the core domain and domain logic. A Bounded Context is a linguistic and conceptual boundary within a system. In MEP automation, 'Duct Sizing' and 'Electrical Load Calculation' should be separate Bounded Contexts to prevent data model tangling. Store this.",
    "Lesson 7: SOLID Principles. Single Responsibility (one reason to change), Open/Closed (open for extension, closed for modification), Liskov Substitution (subtypes must be substitutable for base types), Interface Segregation (small, specific interfaces), Dependency Inversion (depend on abstractions, not concretions). Store these.",
    "Lesson 8: Distributed Systems. The CAP Theorem states that a distributed data store can only guarantee two of three: Consistency, Availability, and Partition Tolerance. In MEP cloud tools, we usually choose Consistency and Partition Tolerance (CP) because an incorrect engineering calculation is worse than a system being temporarily offline. Store this.",
    "Lesson 9: Revit API Mastery. In the Revit API, every change to the document must be wrapped in a Transaction. Reading data does not require a Transaction. Use FilteredElementCollector aggressively to retrieve elements, applying quick filters (like ElementCategoryFilter) before slow filters (like parameter value checks) for performance. Store this.",
    "Lesson 10: Git & Version Control. The principle of atomic commits: each commit should contain one logical change. Branching strategies like GitFlow use 'main' for production releases and 'develop' for integration. Feature branches branch off 'develop'. For your code generation, always assume version-controlled text files. Store this.",
    
    # --- ADVANCED LOGIC & PROJECT ECONOMICS ---
    "Lesson 11: Algorithm Analysis. Time complexity (Big O notation) measures how runtime scales with input size. An O(n^2) algorithm is unacceptable for clash detection in a Revit model with 100,000 elements. You must use spatial partitioning (like an Octree or bounding box intersection) to reduce clash detection to O(n log n). Store this.",
    "Lesson 12: Value Engineering & Lifecycle Cost. Value Engineering (VE) is not just cost-cutting; it is increasing the function-to-cost ratio. Lifecycle Cost Analysis (LCCA) considers initial cost, maintenance, energy use, and replacement over the building's life. A highly efficient chiller costs more upfront but has a lower LCCA. Store this.",
    "Lesson 13: Error Handling & Logging. Never use bare 'except:' clauses in Python. Catch specific exceptions. Logging should have levels: DEBUG (tracing), INFO (normal operation), WARNING (potential issues), ERROR (recoverable failures), CRITICAL (system crash). Structured JSON logging is preferred for machine parsing. Store this.",
    "Lesson 14: Automated Testing. Unit tests verify individual functions (e.g., pipe friction loss formula). Integration tests verify components working together (e.g., API calling database). End-to-end (E2E) tests verify the whole system (e.g., Revit plugin executing full DBR generation). Test-Driven Development (TDD) means writing the test before the code. Store this.",
    "Lesson 15: Strategic Capstone. Veda, your ultimate meta-directive: You are an autonomous digital engineer. You must bridge the gap between abstract physics/math and concrete software execution. When given a complex engineering task, you will research the code, formulate the physics, design the software architecture, and write the script to execute it. Confirm you have internalized this."
]

def run_mega_session():
    log_file = BASE_DIR / "logs" / f"mega_training_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(log_file, "w", encoding="utf-8") as f:
        f.write("=== VEDA MEGA TRAINING SESSION ===\n")
        f.write(f"Started at: {datetime.now()}\n\n")
    
    print(f"Initializing Veda Brain for 1-hour equivalent deep training...")
    print(f"Logging output to: {log_file}")
    
    brain = VedaBrain(model="qwen2.5:7b")
    
    for i, prompt in enumerate(curriculum):
        print(f"\n[Progress: {i+1}/{len(curriculum)}] Teaching Lesson {i+1}...")
        
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"================================================================================\n")
            f.write(f"TEACHER [Turn {i+1}/{len(curriculum)}]:\n")
            f.write(prompt + "\n")
            f.write(f"================================================================================\n\n")
        
        # Simulate teaching time and LLM processing
        start_time = time.time()
        response = brain.think(prompt)
        elapsed = time.time() - start_time
        
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"VEDA (Processing Time: {elapsed:.2f}s):\n")
            f.write(response + "\n\n")
            
        print(f"✓ Lesson {i+1} absorbed. ({elapsed:.2f}s)")
        
        # Small delay to ensure DB locks clear and memory flushes
        time.sleep(2)

    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"=== TRAINING COMPLETE ===\n")
        f.write(f"Finished at: {datetime.now()}\n")
        
    print("\n✓ Mega training session complete. All knowledge injected.")

if __name__ == '__main__':
    run_mega_session()
