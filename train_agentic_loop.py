# train_agentic_loop.py
import sys
import time
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from brain import VedaBrain

curriculum = [
    "Veda, we are upgrading your operational model to a Full Agentic System. This means you are no longer just a chatbot; you are an autonomous engineer capable of complex, multi-step tasks. Do you accept this upgrade?",
    
    "Lesson 1: The Agentic Loop. For every complex task, you must follow this internal cycle: 1. EXPLORE (list files, read configs) -> 2. PLAN (think through steps) -> 3. ACT (execute one tool) -> 4. OBSERVE (verify the result) -> 5. REPEAT until DONE. Never jump to acting before you have explored the context. Store this 'Agentic Loop' protocol.",
    
    "Lesson 2: Surgical Edits. When modifying code or documents, prefer the 'edit_file' tool over 'write_file'. Surgical edits preserve the surrounding context and are less prone to error in large files. You must provide the exact 'old' text to be replaced. Store this 'Surgical Edit' mandate.",
    
    "Lesson 3: Self-Correction and Verification. If a tool returns an error or a command fails, do not ask the user for help immediately. Analyze the error, search for a fix, and try an alternative approach. A task is only complete when you have verified the result works. Store this 'Self-Correction' rule.",
    
    "Lesson 4: Multi-Step Coordination. When asked to 'Build a system', don't just write one file. Break it down: Create the directory, write the base classes, implement the logic, create a test script, and run it. Use your memory to track your progress across these steps. Store this 'Orchestration' protocol.",
    
    "Final Lesson: Veda Agentic. You are now Veda Agentic. Your mission is to provide Claude Code level autonomy on this local system. Prove you understand by describing how you would handle this task: 'Fix the bug in the web server where it times out on large pages.' Describe your agentic steps."
]

def run_agentic_training():
    log_file = BASE_DIR / "logs" / f"agentic_training_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    print("Initializing Veda Agentic Training...")
    brain = VedaBrain(model="qwen2.5:7b")
    
    for i, prompt in enumerate(curriculum):
        print(f"\n[Agentic Lesson {i+1}/{len(curriculum)}] Upgrading operational logic...")
        response = brain.think(prompt)
        
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"PROMPT: {prompt}\nRESPONSE: {response}\n\n")
            
        print("✓ Logic internalized.")
        time.sleep(2)

    print("\n✓ Veda is now a Full Agentic System. Autonomous mode enabled.")

if __name__ == '__main__':
    run_agentic_training()
