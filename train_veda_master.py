# train_veda_master.py
import sys
from pathlib import Path

# Ensure project root is in sys.path
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from memory.semantic import SemanticMemory

def train():
    memory = SemanticMemory()
    training_file = BASE_DIR / "veda_master_training.md"
    
    if not training_file.exists():
        print(f"Error: {training_file} not found.")
        return

    print(f"Reading {training_file.name}...")
    content = training_file.read_text(encoding="utf-8")
    
    # Split by major parts (## PART X)
    parts = content.split("## PART")
    
    loaded_count = 0
    for part in parts:
        part = part.strip()
        if not part:
            continue
            
        part_title = part.split("\n")[0].strip()
        print(f"Processing Part {part_title}...")
        
        # Further split by sub-sections (### X.X) or double newlines for better granularity
        sections = part.split("###")
        for section in sections:
            section = section.strip()
            if not section:
                continue
            
            clean_text = f"VEDA TRAINING DATA - {part_title}\n{section}"
            
            # If the section is too large, split by double newlines
            if len(clean_text) > 2000:
                sub_chunks = clean_text.split("\n\n")
                for chunk in sub_chunks:
                    chunk = chunk.strip()
                    if len(chunk) > 100:
                        memory.store(chunk, metadata={"source": "master_training", "part": part_title})
                        loaded_count += 1
            else:
                if len(clean_text) > 100:
                    memory.store(clean_text, metadata={"source": "master_training", "part": part_title})
                    loaded_count += 1

    print(f"\n✓ Training complete. Loaded {loaded_count} knowledge chunks into Veda's semantic memory.")

if __name__ == "__main__":
    train()
