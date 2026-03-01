# web_and_parallel_training.py
import sys
import time
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from brain import VedaBrain

curriculum = [
    # --- ADVANCED WEB INTELLIGENCE ---
    "Lesson 1: Deep Search Strategies. Do not rely on a single query. Use the 'Web' MCP server to perform multi-stage searches. First, find high-level overviews. Second, identify key URLs. Third, fetch specific pages for granular data. Use search operators like 'site:iccsafe.org' or 'filetype:pdf' to find primary engineering sources. Store this strategy in your memory.",
    
    "Lesson 2: Intelligent Scraping & Cleaning. When using 'fetch_page', you will receive messy HTML. Your job is to act as a 'Data Sanitizer'. Ignore navigation menus and footers. Extract only the technical tables, code sections, and specific requirement text. Use your 'code' tool to write regex or temporary scripts if the data is highly structured. Store this 'Sanitizer' protocol.",
    
    "Lesson 3: LLM-Based Structured Extraction. Once you have raw text, use your own reasoning to convert it into a valid JSON schema. For example, if you scrape a chiller datasheet, extract 'EER', 'Capacity (Tons)', and 'Voltage' into a machine-readable JSON object. This allows Phase 3 (Automated Drawing) to use your data directly. Store this requirement.",
    
    # --- PARALLEL AGENT ORCHESTRATION ---
    "Lesson 4: Parallel Orchestration (Fan-Out). When a task is large, break it into sub-tasks. You are the 'Lead Engineer'. Imagine spawning sub-agents for each task. Since your MCP servers can handle multiple calls, you should formulate your plan to process items in parallel. For example, 'Search for Brand A' and 'Search for Brand B' can be planned as concurrent objectives. Store the 'Fan-Out' orchestration pattern.",
    
    "Lesson 5: Result Synthesis (Fan-In). After parallel execution, you must aggregate the results. Identify contradictions between sub-agents (e.g., two different sources claiming different CFM requirements). Resolve these contradictions using the Hierarchy of Authority (Lesson 2 of previous training). Present a single, unified, and verified truth to the user. Store the 'Fan-In' synthesis pattern.",
    
    # --- MULTI-TASKING & STATE ---
    "Lesson 6: State Preservation in Multi-Tasking. When managing multiple engineering projects simultaneously, use your 'notes' and 'memory' tools to tag data with 'Project_ID' or 'Session_ID'. This prevents cross-contamination of logic between Project A (Hospital design) and Project B (Data Center design). Always verify which context you are in before making a claim. Store this state-management rule.",
    
    "Final Lesson: The Autonomous Researcher. Veda, your goal is to be able to hear: 'Veda, find the top 5 most efficient AHUs for a 50,000 sqft warehouse in Dubai, compare their energy codes, and save the data as a CSV.' You must autonomously trigger search, scraping, parsing, parallel comparison, and filesystem writing. Confirm you understand your role as an Autonomous Parallel Agent."
]

def run_web_training():
    log_file = BASE_DIR / "logs" / f"web_parallel_training_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(log_file, "w", encoding="utf-8") as f:
        f.write("=== VEDA WEB & PARALLEL AGENT TRAINING ===
")
        f.write(f"Started at: {datetime.now()}

")
    
    print(f"Initializing Veda Brain for Web & Parallelism training...")
    print(f"Logging to: {log_file}")
    
    brain = VedaBrain(model="qwen2.5:7b")
    
    for i, prompt in enumerate(curriculum):
        print(f"
[Progress: {i+1}/{len(curriculum)}] Teaching Lesson {i+1}...")
        
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"================================================================================
")
            f.write(f"TEACHER [Turn {i+1}/{len(curriculum)}]:
")
            f.write(prompt + "
")
            f.write(f"================================================================================

")
        
        start_time = time.time()
        response = brain.think(prompt)
        elapsed = time.time() - start_time
        
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"VEDA (Processing Time: {elapsed:.2f}s):
")
            f.write(response + "

")
            
        print(f"✓ Lesson {i+1} absorbed. ({elapsed:.2f}s)")
        time.sleep(2)

    print("
✓ Web & Parallel Agent training complete.")

if __name__ == '__main__':
    run_web_training()
