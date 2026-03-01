# compile_knowledge.py
import sys
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
KNOWLEDGE_DIR = BASE_DIR / "knowledge"

def compile_knowledge():
    print("Compiling hardcoded knowledge base...")
    
    knowledge_base = {
        "mcp_category_mappings": [
            {
                "category": "web",
                "server": "web",
                "primary_tool": "search",
                "description": "Use 'search' for all web queries. Do NOT use 'web'."
            },
            {
                "category": "filesystem",
                "server": "filesystem",
                "primary_tool": "list_directory",
                "description": "Use 'list_directory', 'read_file', 'write_file', 'edit_file'."
            }
        ],
        "mcp_tool_schemas": [
            {
                "server": "filesystem",
                "tools": [
                    {"name": "read_file", "params": ["path"], "example": "TOOL: read_file\nPARAMS: {\"path\": \"file.txt\"}"},
                    {"name": "write_file", "params": ["path", "content"], "example": "TOOL: write_file\nPARAMS: {\"path\": \"script.py\", \"content\": \"print('hi')\"}"},
                    {"name": "edit_file", "params": ["path", "old", "new"], "example": "TOOL: edit_file\nPARAMS: {\"path\": \"file.txt\", \"old\": \"wrong\", \"new\": \"right\"}"},
                    {"name": "list_directory", "params": ["path", "recursive", "pattern"], "example": "TOOL: list_directory\nPARAMS: {\"path\": \".\"}"}
                ]
            },
            {
                "server": "code",
                "tools": [
                    {"name": "run_python", "params": ["code", "timeout"], "example": "TOOL: run_python\nPARAMS: {\"code\": \"import math\\nprint(math.pi)\"}"},
                    {"name": "run_shell", "params": ["command", "timeout", "confirm"], "example": "TOOL: run_shell\nPARAMS: {\"command\": \"pip list\", \"confirm\": true}"}
                ]
            },
            {
                "server": "simulation",
                "tools": [
                    {"name": "calc_psychrometrics", "params": ["dry_bulb_f", "relative_humidity_pct"]},
                    {"name": "calc_pipe_friction", "params": ["flow_gpm", "diameter_inches", "length_ft"]}
                ]
            }
        ],
        "automation_logic": [
            {
                "topic": "The Bridge Pattern",
                "content": "To perform custom tasks: 1. Use 'write_file' to save a .py script. 2. Use 'run_python' or 'run_shell' to execute it. 3. Read the output to verify."
            },
            {
                "topic": "System Capabilities",
                "content": "You have 'pandas', 'matplotlib.pyplot', 'fitz' (PyMuPDF), and 'requests' installed in your local environment. Use them for data, charts, PDFs, and APIs."
            }
        ],
        "mep_first_principles": [
            {
                "topic": "Fluid Mechanics",
                "content": "Use Hazen-Williams for pipe pressure drop. Mandated tool: calc_pipe_friction(flow_gpm, diameter_inches, length_ft)."
            }
        ]
    }
    
    KNOWLEDGE_DIR.mkdir(exist_ok=True)
    with open(KNOWLEDGE_DIR / "core_knowledge.json", "w", encoding="utf-8") as f:
        json.dump(knowledge_base, f, indent=4)
        
    print("✓ Hardcoded knowledge compiled with Examples.")

if __name__ == "__main__":
    compile_knowledge()
