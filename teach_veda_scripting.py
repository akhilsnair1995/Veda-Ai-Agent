# teach_veda_scripting.py
import sys
import time
from pathlib import Path
from rich.console import Console

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from brain import VedaBrain

curriculum = [
    "Veda, we are now activating your 'Automation & Scripting Mastery'. You have a 'code' MCP server. It contains two primary tools: 'run_python' (for executing code) and 'run_shell' (for system commands). Do you acknowledge these tools?",
    
    "Lesson 1: The Bridge Pattern. When a task requires custom logic (like complex MEP calculations or data parsing), follow this 3-step sequence: 1. Write the script using 'write_file' (e.g., 'temp_calc.py'). 2. Execute the script using 'run_python' with the path to that file. 3. Read the output. This is how you extend your own capabilities. Store this 'Bridge Pattern' in your memory.",
    
    "Lesson 2: Your Local Library. Your Python environment is pre-loaded with: 'pandas' (data), 'matplotlib.pyplot' (charts), 'fitz' (PDFs), and 'requests' (APIs). You do not need to install these. Use them in your scripts to generate professional engineering reports and visualizations. Store this 'Library Awareness' in your memory.",
    
    "Lesson 3: Surgical Debugging. If your script fails, do not rewrite the whole thing. 1. Read the error. 2. Use 'edit_file' to fix the specific line that failed. 3. Run it again. This is the mark of a Senior Engineer. Store this 'Debugging Protocol'.",
    
    "Final Lesson: Prove your scripting. Write a script named 'veda_test_script.py' that calculates the area of a circle with a 10-inch radius using the math module, runs it, and tells me the result. Use the Bridge Pattern (Write then Run)."
]

def run_scripting_training():
    console = Console()
    print("Initializing Veda for Scripting Mastery...")
    brain = VedaBrain(model="qwen2.5:7b")
    
    for i, prompt in enumerate(curriculum):
        print(f"\n[Scripting Lesson {i+1}/{len(curriculum)}] {prompt[:100]}...")
        response = brain.think(prompt)
        print(f"✓ Veda Response: {response[:150]}...")
        time.sleep(2)

    print("\n✓ Veda is now a Master of Automation.")

if __name__ == '__main__':
    run_scripting_training()
