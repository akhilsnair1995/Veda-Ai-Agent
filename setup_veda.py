# setup_veda.py — AUTOMATED INITIALIZATION
import os
import subprocess
import sys
import json
from pathlib import Path

# Add Veda's core folder to path
VEDA_ROOT = Path(__file__).resolve().parent
if str(VEDA_ROOT) not in sys.path:
    sys.path.insert(0, str(VEDA_ROOT))

def run_cmd(cmd, description):
    print(f"\n--- {description} ---")
    try:
        # Use powershell on windows
        if os.name == 'nt':
            subprocess.run(["powershell.exe", "-Command", cmd], check=True)
        else:
            subprocess.run(cmd, shell=True, check=True)
        return True
    except Exception as e:
        print(f"✗ Error during {description}: {e}")
        return False

def setup():
    print("\n--- VEDA: UNIVERSAL AGENT INITIALIZATION ---\n")
    
    # 1. Ensure Dependencies are available
    # (Assuming the user is already in the venv as per instructions)

    # 2. Create Ollama Model
    modelfile_path = VEDA_ROOT / "knowledge" / "Modelfile.veda"
    # Ensure Modelfile exists in knowledge for others
    if not modelfile_path.exists():
        content = 'FROM qwen2.5:7b\nSYSTEM "You are Veda, an autonomous AI agent..."\n'
        modelfile_path.parent.mkdir(exist_ok=True)
        modelfile_path.write_text(content)
        
    run_cmd(f"ollama create veda -f '{modelfile_path}'", "Creating Ollama model 'veda'")

    # 3. Seed Memory from Knowledge Directory
    from memory.semantic import SemanticMemory
    print("\n--- Seeding Universal Knowledge Base ---")
    memory = SemanticMemory()
    knowledge_dir = VEDA_ROOT / "knowledge"
    
    count = 0
    # Seed JSONL files
    for jsonl_file in knowledge_dir.glob("*.jsonl"):
        print(f"Reading {jsonl_file.name}...")
        with open(jsonl_file, 'r', encoding='utf-8') as f:
            for line in f:
                data = json.loads(line)
                msgs = data.get('messages', [])
                if len(msgs) >= 2:
                    content = f"EXAMPLE_Q: {msgs[0]['content']}\nEXAMPLE_A: {msgs[1]['content']}"
                    memory.store(content, metadata={"source": jsonl_file.name, "type": "example"})
                    count += 1
    
    # Seed Markdown Guide
    guide_path = knowledge_dir / "VEDA_GEMINI_TRAINING_GUIDE.md"
    if guide_path.exists():
        print(f"Reading {guide_path.name}...")
        content = guide_path.read_text(encoding='utf-8')
        memory.store(content, metadata={"source": "training_guide", "type": "manual"})
        count += 1

    print(f"✓ Seeded {count} universal knowledge items into local memory.")
    print("\n--- Veda is now fully initialized and ready to work. ---")

if __name__ == "__main__":
    setup()
