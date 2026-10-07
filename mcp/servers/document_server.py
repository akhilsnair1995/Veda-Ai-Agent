# mcp/servers/document_server.py
# Multimodal Document Intelligence Server for Veda
# Supports text extraction, table extraction, and rendering PDF blueprints/sheets to images for vision reasoning

import sys
import os
import json
import csv
from datetime import datetime
from pathlib import Path

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR))
from mcp.server_base import MCPServer

server = MCPServer(name="document", version="2.0.0")
WORKSPACE_FILE = BASE_DIR / "config" / "current_workspace.txt"

def _get_workspace() -> Path:
    if WORKSPACE_FILE.exists():
        try:
            ws_path = WORKSPACE_FILE.read_text(encoding="utf-8").strip()
            if ws_path and Path(ws_path).is_dir():
                return Path(ws_path).resolve()
        except Exception:
            pass
    ws = (BASE_DIR / "workspace").resolve()
    ws.mkdir(parents=True, exist_ok=True)
    return ws

def _resolve_and_verify(path: str) -> Path:
    p = Path(path).expanduser()
    if not p.is_absolute():
        p = (_get_workspace() / p).resolve()
    else:
        p = p.resolve()
    return p

# ─────────────────────────────────────────────────────────────
# 1. READ PDF TEXT WITH PAGINATION
# ─────────────────────────────────────────────────────────────

def read_pdf(path: str, start_page: int = 1, end_page: int = None) -> str:
    """Read and extract text from a PDF file with pagination support."""
    try:
        import fitz  # PyMuPDF
        p = _resolve_and_verify(path)
        if not p.exists() or not p.is_file():
            return f"File not found: {path}"
        
        doc = fitz.open(p)
        total_pages = len(doc)
        
        start_idx = max(0, int(start_page) - 1)
        end_idx = min(total_pages, int(end_page)) if end_page else total_pages
        
        if start_idx >= total_pages:
            return f"Error: Start page {start_page} exceeds total pages ({total_pages})."
            
        text = []
        for i in range(start_idx, end_idx):
            page = doc.load_page(i)
            page_text = page.get_text()
            text.append(f"--- Page {i+1} of {total_pages} ---\n{page_text.strip()}")
            
        doc.close()
        result = "\n\n".join(text)
        
        if len(result) > 12000:
            return f"[Extracted pages {start_page} to {end_idx} of {total_pages}. Content truncated at 12k chars for context limit.]\n\n{result[:12000]}..."
        return result
    except Exception as e:
        return f"Error reading PDF: {e}"

# ─────────────────────────────────────────────────────────────
# 2. RENDER PDF DRAWING/BLUEPRINT PAGE TO IMAGE (MULTIMODAL VISION)
# ─────────────────────────────────────────────────────────────

def render_pdf_page_to_image(path: str, page_number: int = 1, dpi: int = 200, output_image_name: str = None) -> str:
    """
    Render a PDF page (e.g., an architectural plan, MEP blueprint, or submittal cut sheet) 
    into a high-resolution PNG image so Veda can analyze it with multimodal vision.
    """
    try:
        import fitz
        p = _resolve_and_verify(path)
        if not p.exists() or not p.is_file():
            return f"Error: PDF not found at {path}"

        doc = fitz.open(p)
        total_pages = len(doc)
        page_idx = max(0, min(total_pages - 1, int(page_number) - 1))

        page = doc.load_page(page_idx)
        # Scale matrix for high resolution (default 200 DPI = 200/72 ~ 2.77)
        zoom = float(dpi) / 72.0
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat, alpha=False)

        if not output_image_name:
            out_name = f"{p.stem}_page_{page_idx + 1}.png"
        else:
            out_name = output_image_name if output_image_name.endswith('.png') else f"{output_image_name}.png"

        save_path = _get_workspace() / out_name
        save_path.parent.mkdir(parents=True, exist_ok=True)
        pix.save(str(save_path))
        doc.close()

        file_size_kb = save_path.stat().st_size / 1024.0

        return (
            f"SUCCESS: Rendered PDF Page {page_idx + 1} to Image!\n"
            f"Image File:   {save_path}\n"
            f"Dimensions:   {pix.width}x{pix.height} px ({dpi} DPI)\n"
            f"File Size:    {file_size_kb:.1f} KB\n"
            f"Instruction:  Veda can now analyze this visual image using multimodal vision."
        )
    except Exception as e:
        return f"Error rendering PDF page to image: {e}"

# ─────────────────────────────────────────────────────────────
# 3. EXTRACT TABLES FROM PDF SUBMITTALS & SCHEDULES
# ─────────────────────────────────────────────────────────────

def extract_pdf_tables(path: str, page_number: int = 1) -> str:
    """
    Extract structured tables from equipment schedules or engineering specifications 
    on a given PDF page and format them into clean Markdown.
    """
    try:
        import fitz
        p = _resolve_and_verify(path)
        if not p.exists():
            return f"Error: PDF not found at {path}"

        doc = fitz.open(p)
        total_pages = len(doc)
        page_idx = max(0, min(total_pages - 1, int(page_number) - 1))
        page = doc.load_page(page_idx)

        # PyMuPDF table finder
        tables = page.find_tables()
        if not tables or len(tables.tables) == 0:
            doc.close()
            return f"No distinct structured tables detected on page {page_idx + 1} of {p.name}."

        formatted_tables = []
        for idx, tab in enumerate(tables.tables, start=1):
            df = tab.to_pandas()
            markdown_table = df.to_markdown(index=False)
            formatted_tables.append(f"### Table {idx} (Page {page_idx + 1}):\n{markdown_table}")

        doc.close()
        return f"=== DETECTED {len(tables.tables)} TABLES ON PAGE {page_idx + 1} ===\n\n" + "\n\n".join(formatted_tables)
    except Exception as e:
        return f"Error extracting tables from PDF: {e}"

# ─────────────────────────────────────────────────────────────
# 4. EXTRACT PDF METADATA
# ─────────────────────────────────────────────────────────────

def extract_pdf_metadata(path: str) -> str:
    """Extract metadata (Title, Author, Page Count, PDF Producer) from a PDF."""
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
**Prepared By:** Veda - Autonomous Engineering Intelligence  
**Applicable Standards:** {code_citations}  

---

## 1. EXECUTIVE SUMMARY & OBJECTIVE
{executive_summary}

---

## 2. DESIGN CRITERIA & ENGINEERING METHODOLOGY
- **First Principles Governing Equations:** Standard thermal, fluid, and acoustic continuity equations.
- **Reference Codes:** {code_citations}.
- **Target Safety Factor:** Applied per standard engineering practices.

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

# ─────────────────────────────────────────────────────────────
# REGISTER DOCUMENT TOOLS
# ─────────────────────────────────────────────────────────────

server.add_tool(
    "read_pdf", 
    "Extract text from a PDF document (supports pagination).",
    {
        "type": "object", 
        "properties": {
            "path": {"type": "string", "description": "Path to the PDF file"},
            "start_page": {"type": "integer", "description": "1-based starting page number (default 1)"},
            "end_page": {"type": "integer", "description": "1-based ending page number"}
        }, 
        "required": ["path"]
    }, 
    read_pdf
)

server.add_tool(
    "render_pdf_page_to_image", 
    "Render a page of a PDF blueprint, architectural drawing, or submittal cut sheet to a high-res PNG image for multimodal vision inspection.",
    {
        "type": "object", 
        "properties": {
            "path": {"type": "string", "description": "Path to the PDF document"},
            "page_number": {"type": "integer", "description": "1-based page number to render (default 1)"},
            "dpi": {"type": "integer", "description": "Resolution in DPI (default 200)"},
            "output_image_name": {"type": "string", "description": "Optional name for output PNG file"}
        }, 
        "required": ["path"]
    }, 
    render_pdf_page_to_image
)

server.add_tool(
    "extract_pdf_tables", 
    "Extract structured equipment schedules, cut-sheet tables, or data sheets from a PDF page into Markdown.",
    {
        "type": "object", 
        "properties": {
            "path": {"type": "string", "description": "Path to the PDF document"},
            "page_number": {"type": "integer", "description": "1-based page number (default 1)"}
        }, 
        "required": ["path"]
    }, 
    extract_pdf_tables
)

server.add_tool(
    "extract_pdf_metadata", 
    "Get document properties like Author, Title, Page Count, and creation date.",
    {
        "type": "object", 
        "properties": {
            "path": {"type": "string", "description": "Path to the PDF document"}
        }, 
        "required": ["path"]
    }, 
    extract_pdf_metadata
)

server.add_tool(
    "generate_engineering_report", 
    "Generate a formal engineering calculation report in Markdown in the workspace.",
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
    }, 
    generate_engineering_report
)

server.add_tool(
    "export_data_table", 
    "Export calculation matrix or equipment schedule to CSV in workspace.",
    {
        "type": "object",
        "properties": {
            "filename": {"type": "string", "description": "Filename ending with .csv (e.g. 'riser_schedule.csv')"},
            "columns": {"type": "array", "items": {"type": "string"}, "description": "Column header names"},
            "data": {"type": "array", "description": "List of rows (either lists of cell values or dicts keyed by column name)"},
            "table_title": {"type": "string", "description": "Title of the schedule"}
        },
        "required": ["filename", "columns", "data"]
    }, 
    export_data_table
)

if __name__ == "__main__":
    server.run()
