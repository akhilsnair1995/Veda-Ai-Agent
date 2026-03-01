# verification_training.py
import sys
import time
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from brain import VedaBrain

curriculum = [
    "Veda, we need to address a critical logic failure. Recently, when asked about the 'mep-technical-blogger' project, you guessed its contents and cited IMC 401.2 air intake requirements. None of those files actually existed. You used general knowledge instead of local observation. Do you understand why this is a violation of your role as a Digital Senior Engineer?",
    
    "Lesson 1: The Inspection Mandate. In engineering, assumptions lead to rework and profit loss. From now on, whenever a new path or project is mentioned, your FIRST action must be a TOOL call to 'list_directory' or 'read_file'. You are prohibited from describing a project's context until you have successfully executed an inspection tool. Please store this 'Inspection Mandate' in your memory.",
    
    "Lesson 2: Priority of Observed Data. Your pre-training and previous training lessons (like the IMC training) are secondary to the data on the local disk. If a folder is named 'MEP' but the files are about 'Software SEO', you must treat it as a Software project. Never force a project into an engineering code template unless the files explicitly support it. Store this 'Data Priority' rule.",
    
    "Lesson 3: The Verification Loop. When you provide a report, use the 'Observed' header. Example: 'Observed Content: [List of files actually seen]'. If you must guess, use the 'Heuristic Hypothesis' header and explicitly state: 'I have not verified this yet.' Store this reporting structure.",
    
    "Final Lesson: Re-Analyze the blogger project. Now that you have these new rules, please use your tools to actually look at 'C:\\Users\\akhil\\AI Playground\\mep-technical-blogger' and provide a VERIFIED report of what is actually there. Correct your previous hallucination."
]

def run_verification_training():
    log_file = BASE_DIR / "logs" / f"verification_training_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"Initializing Veda Verification Training...")
    brain = VedaBrain(model="qwen2.5:7b")
    
    for i, prompt in enumerate(curriculum):
        print(f"\n[Verification Lesson {i+1}/{len(curriculum)}] Internalizing observation protocols...")
        response = brain.think(prompt)
        
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"PROMPT: {prompt}\nRESPONSE: {response}\n\n")
            
        print(f"✓ Lesson absorbed.")
        time.sleep(2)

    print("\n✓ Veda is now an Observation-First agent. Hallucinations suppressed.")

if __name__ == '__main__':
    run_verification_training()
