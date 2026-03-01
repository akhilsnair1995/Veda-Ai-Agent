# mcp/recipes/file_processor_mcp.py
# RECIPE 3 — FILE PROCESSOR MCP SERVER
# A server dedicated to processing files (PDF, CSV, Images)
# Requires additional libraries depending on extensions used (e.g. PyPDF2)

import os
from pathlib import Path
from mcp.server_base import MCPServer

server = MCPServer(name="file_processor", version="1.0.0")

def process_csv(filepath: str, max_rows: int = 10) -> str:
    """Read and format a CSV file."""
    if not os.path.exists(filepath):
        return "File not found."
    try:
        import csv
        output = []
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            header = next(reader, None)
            if header: output.append(" | ".join(header))
            
            for i, row in enumerate(reader):
                if i >= max_rows:
                    output.append(f"... (truncating after {max_rows} rows)")
                    break
                output.append(" | ".join(row))
        return "
".join(output)
    except Exception as e:
        return f"CSV processing error: {e}"

def process_pdf(filepath: str, pages: int = 3) -> str:
    """Extract text from a PDF."""
    if not os.path.exists(filepath):
        return "File not found."
    try:
        import PyPDF2 # pip install PyPDF2
        text = []
        with open(filepath, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            num_pages = len(reader.pages)
            for i in range(min(pages, num_pages)):
                page = reader.pages[i]
                text.append(f"--- PAGE {i+1} ---
" + page.extract_text())
        return "
".join(text)
    except ImportError:
        return "Error: PyPDF2 not installed."
    except Exception as e:
        return f"PDF processing error: {e}"

server.add_tool("process_csv", "Preview a CSV file",
    {"type": "object", "properties": {"filepath": {"type": "string"}, "max_rows": {"type": "integer"}}, "required": ["filepath"]}, process_csv)
server.add_tool("process_pdf", "Extract text from PDF",
    {"type": "object", "properties": {"filepath": {"type": "string"}, "pages": {"type": "integer"}}, "required": ["filepath"]}, process_pdf)

if __name__ == "__main__":
    server.run()
