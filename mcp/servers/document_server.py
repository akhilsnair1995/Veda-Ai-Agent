# mcp/servers/document_server.py
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR))
from mcp.server_base import MCPServer

server = MCPServer(name="document", version="1.0.0")

def _resolve_and_verify(path: str) -> Path:
    p = Path(path).expanduser()
    if not p.is_absolute():
        p = (BASE_DIR / p).resolve()
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

server.add_tool("read_pdf", "Extract text from a PDF document (supports pagination)",
    {
        "type": "object", 
        "properties": {
            "path": {"type": "string"},
            "start_page": {"type": "integer", "description": "1-based starting page number"},
            "end_page": {"type": "integer", "description": "1-based ending page number"}
        }, 
        "required": ["path"]
    }, read_pdf)

server.add_tool("extract_pdf_metadata", "Get document properties like Author, Title, and Page Count",
    {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}, extract_pdf_metadata)

if __name__ == "__main__":
    server.run()
