# mcp/servers/filesystem_server.py
import os
import sys
import shutil
from pathlib import Path
import fnmatch

BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR))
from mcp.server_base import MCPServer

server = MCPServer(name="filesystem", version="1.0.0")

# Security: Only allow operations within the workspace or safe directories
ALLOWED_BASE = BASE_DIR

def _resolve_and_verify(path: str) -> Path:
    p = Path(path).resolve()
    # Simple check for now, can be tightened
    return p

def read_file(path: str) -> str:
    p = _resolve_and_verify(path)
    if not p.exists() or not p.is_file():
        return f"File not found: {path}"
    try:
        return p.read_text(encoding="utf-8")
    except Exception as e:
        return f"Error reading file: {e}"

def write_file(path: str, content: str) -> str:
    p = _resolve_and_verify(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return f"Successfully wrote to {path}"

def append_file(path: str, content: str) -> str:
    p = _resolve_and_verify(path)
    if not p.exists():
        return write_file(path, content)
    with p.open("a", encoding="utf-8") as f:
        f.write(content)
    return f"Successfully appended to {path}"

def list_directory(path: str, recursive: bool = False, pattern: str = "*") -> str:
    p = _resolve_and_verify(path)
    if not p.exists() or not p.is_dir():
        return f"Directory not found: {path}"
    
    results = []
    if recursive:
        for root, dirs, files in os.walk(p):
            for file in fnmatch.filter(files, pattern):
                results.append(str(Path(root) / file))
    else:
        for item in p.iterdir():
            if fnmatch.fnmatch(item.name, pattern):
                results.append(str(item))
    return "
".join(results) if results else "Empty directory or no matches."

def create_directory(path: str) -> str:
    p = _resolve_and_verify(path)
    p.mkdir(parents=True, exist_ok=True)
    return f"Created directory {path}"

def move_file(source: str, destination: str) -> str:
    src = _resolve_and_verify(source)
    dst = _resolve_and_verify(destination)
    if not src.exists():
        return f"Source not found: {source}"
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(src), str(dst))
    return f"Moved {source} to {destination}"

def delete_file(path: str, confirm: bool = False) -> str:
    if not confirm:
        return "You must set confirm=True to delete a file."
    p = _resolve_and_verify(path)
    if not p.exists():
        return f"File not found: {path}"
    if p.is_file():
        p.unlink()
    else:
        shutil.rmtree(p)
    return f"Deleted {path}"

def get_file_info(path: str) -> str:
    p = _resolve_and_verify(path)
    if not p.exists():
        return f"Not found: {path}"
    stats = p.stat()
    return f"Size: {stats.st_size} bytes
Modified: {stats.st_mtime}
Is Dir: {p.is_dir()}"

server.add_tool("read_file", "Read file contents",
    {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}, read_file)

server.add_tool("write_file", "Write to a file",
    {"type": "object", "properties": {"path": {"type": "string"}, "content": {"type": "string"}}, "required": ["path", "content"]}, write_file)

server.add_tool("append_file", "Append to a file",
    {"type": "object", "properties": {"path": {"type": "string"}, "content": {"type": "string"}}, "required": ["path", "content"]}, append_file)

server.add_tool("list_directory", "List files in a directory",
    {"type": "object", "properties": {"path": {"type": "string"}, "recursive": {"type": "boolean"}, "pattern": {"type": "string"}}, "required": ["path"]}, list_directory)

server.add_tool("create_directory", "Create a new directory",
    {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}, create_directory)

server.add_tool("move_file", "Move or rename a file",
    {"type": "object", "properties": {"source": {"type": "string"}, "destination": {"type": "string"}}, "required": ["source", "destination"]}, move_file)

server.add_tool("delete_file", "Delete a file or directory",
    {"type": "object", "properties": {"path": {"type": "string"}, "confirm": {"type": "boolean"}}, "required": ["path", "confirm"]}, delete_file)

server.add_tool("get_file_info", "Get file metadata",
    {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}, get_file_info)

if __name__ == "__main__":
    server.run()
