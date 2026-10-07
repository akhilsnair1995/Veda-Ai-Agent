# mcp/servers/document_server.py
# Veda Document Intelligence & Engineering Deliverables Server

import sys
import os
import csv
import json
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR))
from mcp.server_base import MCPServer

server = MCPServer(name="document", version="2.0.0")

WORKSPACE_FILE = BASE_DIR / "config" / "current_workspace.txt"

def _get_workspace() -> Path:
    if WORKSPACE_FILE.exists():
        try:
            ws_path = WORKSPACE_FILE.read_text(encoding="utf-8").strip()
            if ws_path:
                p = Path(ws_path).expanduser().resolve()
                if p.is_dir():
                    return p
        except Exception:
            pass
    default_ws = (BASE_DIR / "workspace").resolve()
    default_ws.mkdir(parents=True, exist_ok=True)
    return default_ws

def _resolve_and_verify(path: str) -> Path:
    p = Path(path).expanduser()
    if not p.is_absolute():
        p = (_get_workspace() / p).resolve()
    else:
        p = p.resolve()
    return p

def read_pdf(path: str, start_page: int = 1, end_page: int = None) -> str:
    """Read and extract text from a PDF file."""
    try:
        import fitz  # PyMuPDF
        p = _resolve_and_verify(path)
        if not p.exists() or not p.is_file():
            return f"File not found: {path}"
        
        doc = fitz.open(p)
        total_pages = len(doc)
        
        start_idx = max(0, start_page - 1)
        end_idx = min(total_pages, end_page) if end_page else total_pages
        
        if start_idx >= total_pages:
            return f"Error: Start page {start_page} exceeds total pages ({total_pages})."
            
        text = []
        for i in range(start_idx, end_idx):
            page = doc.load_page(i)
            text.append(f"--- Page {i+1} ---\n{page.get_text()}")
            
        doc.close()
        result = "\n".join(text)
        
        if len(result) > 10000:
            return f"[Extracted {total_pages} pages. Truncated at 10k chars. Specify start_page and end_page to read chunks.]\n\n{result[:10000]}..."
        return result
    except Exception as e:
        return f"Error reading PDF: {e}"

def extract_pdf_metadata(path: str) -> str:
    """Extract metadata (title, author, creation date, etc.) from a PDF."""
    try:
        import fitz
        p = _resolve_and_verify(path)
        if not p.exists() or not p.is_file():
            return f"File not found: {path}"
            
        doc = fitz.open(p)
        metadata = doc.metadata
        page_count = len(doc)
        doc.close()
        
        info = [f"Metadata for {p.name}:", f"Total Pages: {page_count}"]
        for key, value in metadata.items():
            if value:
                info.append(f"{key.capitalize()}: {value}")
                
        return "\n".join(info)
    except Exception as e:
        return f"Error extracting metadata: {e}"

def generate_engineering_report(project_name: str, executive_summary: str, calculations_body: str, recommendations: str, discipline: str = "MEP Engineering", code_citations: str = "ASHRAE / IMC / SMACNA", save_filename: str = None) -> str:
    """
    Generate a formal engineering calculation report in Markdown and save it to the workspace.
    """
    try:
        ws = _get_workspace()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        date_slug = datetime.now().strftime("%Y%m%d_%H%M")
        
        if not save_filename:
            safe_title = "".join(c if c.isalnum() or c in ['-', '_'] else '_' for c in project_name.lower().replace(" ", "_"))
            save_filename = f"report_{safe_title}_{date_slug}.md"
            
        out_path = ws / save_filename
        
        report_md = f"""# ENGINEERING CALCULATION REPORT & DESIGN BRIEF
**Project:** {project_name}  
**Discipline:** {discipline}  
**Date Generated:** {timestamp}  
**Prepared By:** Veda — Autonomous Engineering Intelligence  
**Applicable Standards:** {code_citations}  

---

## 1. EXECUTIVE SUMMARY & OBJECTIVE
{executive_summary}

---

## 2. DESIGN CRITERIA & ENGINEERING METHODOLOGY
- **First Principles Governing Equations:** Standard thermal, fluid, and acoustic continuity equations.
- **Reference Codes:** {code_citations}.
- **Target Safety Factor:** Applied per standard practice.

---

## 3. CALCULATIONS & TECHNICAL EVALUATION
{calculations_body}

---

## 4. CODE COMPLIANCE CITATIONS
{code_citations}

---

## 5. PRACTICAL RECOMMENDATIONS & ACTION ITEMS
{recommendations}

---
*Report certified by Veda AI Engineering Core • Generated in active workspace `{ws}`*
"""
        out_path.write_text(report_md, encoding="utf-8")
        return f"Successfully generated engineering report and saved to:\n{out_path}\n(Total length: {len(report_md)} characters)"
    except Exception as e:
        return f"Error generating engineering report: {e}"

def export_data_table(filename: str, columns: list, data: list, table_title: str = "Engineering Schedule") -> str:
    """
    Export calculation matrix or equipment schedule to CSV and formatted Markdown table in workspace.
    """
    try:
        ws = _get_workspace()
        if not filename.endswith(".csv"):
            filename += ".csv"
        csv_path = ws / filename
        
        with open(csv_path, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(columns)
            for row in data:
                if isinstance(row, dict):
                    writer.writerow([row.get(col, "") for col in columns])
                elif isinstance(row, (list, tuple)):
                    writer.writerow(row)
                else:
                    writer.writerow([str(row)])

        return f"Successfully exported '{table_title}' ({len(data)} rows) to CSV at:\n{csv_path}"
    except Exception as e:
        return f"Error exporting table: {e}"

# Register Tools
server.add_tool("read_pdf", "Extract text from a PDF document (supports pagination)",
    {
        "type": "object", 
        "properties": {
            "path": {"type": "string", "description": "Path to PDF file"},
            "start_page": {"type": "integer", "description": "1-based starting page number"},
            "end_page": {"type": "integer", "description": "1-based ending page number"}
        }, 
        "required": ["path"]
    }, read_pdf)

server.add_tool("extract_pdf_metadata", "Get document properties like Author, Title, and Page Count",
    {"type": "object", "properties": {"path": {"type": "string", "description": "Path to PDF file"}}, "required": ["path"]}, extract_pdf_metadata)

server.add_tool("generate_engineering_report", "Generate a formal engineering calculation report in Markdown in the workspace",
    {
        "type": "object",
        "properties": {
            "project_name": {"type": "string", "description": "Project title (e.g. 'St. Mary Hospital Exhaust Riser Study')"},
            "executive_summary": {"type": "string", "description": "Concise summary of the problem and engineering conclusion"},
            "calculations_body": {"type": "string", "description": "Detailed calculation steps, formulas, and numeric results"},
            "recommendations": {"type": "string", "description": "Actionable engineering recommendations and mitigations"},
            "discipline": {"type": "string", "description": "Engineering discipline (e.g. 'MEP - HVAC', 'Electrical', 'Structural')"},
            "code_citations": {"type": "string", "description": "Applicable codes (e.g. 'ASHRAE 62.1, IMC 2021, SMACNA')"},
            "save_filename": {"type": "string", "description": "Optional custom filename (e.g. 'exhaust_riser_report.md')"}
        },
        "required": ["project_name", "executive_summary", "calculations_body", "recommendations"]
    }, generate_engineering_report)

server.add_tool("export_data_table", "Export calculation matrix or equipment schedule to CSV in workspace",
    {
        "type": "object",
        "properties": {
            "filename": {"type": "string", "description": "Filename ending with .csv (e.g. 'riser_schedule.csv')"},
            "columns": {"type": "array", "items": {"type": "string"}, "description": "Column header names"},
            "data": {"type": "array", "description": "List of rows (either lists of cell values or dicts keyed by column name)"},
            "table_title": {"type": "string", "description": "Title of the schedule"}
        },
        "required": ["filename", "columns", "data"]
    }, export_data_table)

if __name__ == "__main__":
    server.run()
