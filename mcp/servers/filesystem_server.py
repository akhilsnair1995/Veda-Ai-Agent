# mcp/servers/filesystem_server.py
import os
import sys
import shutil
import fnmatch
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR))
from mcp.server_base import MCPServer

server = MCPServer(name="filesystem", version="1.0.0")

def _human_size(size: int) -> str:
    """Convert bytes to human readable string."""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} PB"

WORKSPACE_DIR = BASE_DIR / "workspace"

def _resolve_and_verify(path: str) -> Path:
    # Resolve relative paths against the dedicated workspace
    p = Path(path).expanduser()
    if not p.is_absolute():
        p = (WORKSPACE_DIR / p).resolve()
    else:
        p = p.resolve()
    return p

def read_file(path: str = None, file_path: str = None) -> str:
    path = path or file_path
    if not path:
        return "Error: path is required."
    p = _resolve_and_verify(path)
    if not p.exists() or not p.is_file():
        return f"File not found: {path}"
    
    try:
        size = p.stat().st_size
        if size > 1_000_000:  # 1MB limit
            return f"File is very large ({_human_size(size)}). Reading first 5000 chars:\n\n" + \
                   p.read_text(encoding="utf-8", errors="replace")[:5000]
        return p.read_text(encoding="utf-8")
    except Exception as e:
        return f"Error reading file: {e}"

def write_file(path: str = None, content: str = "", file_path: str = None) -> str:
    path = path or file_path
    if not path:
        return "Error: path is required."
    try:
        p = _resolve_and_verify(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        return f"Successfully wrote to {path}"
    except Exception as e:
        return f"Error writing file: {e}"

def append_file(path: str, content: str) -> str:
    try:
        p = _resolve_and_verify(path)
        if not p.exists():
            return write_file(path, content)
        with p.open("a", encoding="utf-8") as f:
            f.write(content)
        return f"Successfully appended to {path}"
    except Exception as e:
        return f"Error appending file: {e}"

def list_directory(path: str, recursive: bool = False, pattern: str = "*") -> str:
    try:
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
        return "\n".join(results) if results else "Empty directory or no matches."
    except Exception as e:
        return f"Error listing directory: {e}"

def create_directory(path: str) -> str:
    try:
        p = _resolve_and_verify(path)
        p.mkdir(parents=True, exist_ok=True)
        return f"Created directory {path}"
    except Exception as e:
        return f"Error creating directory: {e}"

def move_file(source: str, destination: str) -> str:
    try:
        src = _resolve_and_verify(source)
        dst = _resolve_and_verify(destination)
        if not src.exists():
            return f"Source not found: {source}"
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dst))
        return f"Moved {source} to {destination}"
    except Exception as e:
        return f"Error moving file: {e}"

def delete_file(path: str, confirm: bool = False) -> str:
    if not confirm:
        return "You must set confirm=True to delete a file."
    try:
        p = _resolve_and_verify(path)
        if not p.exists():
            return f"File not found: {path}"
        if p.is_file():
            p.unlink()
        else:
            shutil.rmtree(p)
        return f"Deleted {path}"
    except Exception as e:
        return f"Error deleting file: {e}"
def edit_file(path: str = None, old: str = None, new: str = None, file_path: str = None) -> str:
    """Surgical text replacement in a file."""
    path = path or file_path
    try:
        p = _resolve_and_verify(path)
        if not p.exists():
            return f"File not found: {path}"
        content = p.read_text(encoding="utf-8")

        if old not in content:
            return f"ERROR: Exact text to replace not found in {path}. Ensure 'old' string matches exactly."

        count = content.count(old)
        if count > 1:
            return f"ERROR: Found {count} occurrences of the text. Please provide more context to make the replacement unique."

        new_content = content.replace(old, new)
        p.write_text(new_content, encoding="utf-8")
        return f"Successfully edited {path}. Replaced 1 occurrence."
    except Exception as e:
        return f"Error editing file: {e}"

def replace_text(path: str, old_string: str, new_string: str) -> str:
    """
    High-precision replacement tool. 
    Requires the exact old_string to be replaced with new_string.
    """
    return edit_file(path=path, old=old_string, new=new_string)

def get_file_info(path: str) -> str:

    try:
        p = _resolve_and_verify(path)
        if not p.exists():
            return f"Not found: {path}"
        stats = p.stat()
        return f"Size: {stats.st_size} bytes\nModified: {stats.st_mtime}\nIs Dir: {p.is_dir()}"
    except Exception as e:
        return f"Error getting file info: {e}"

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

server.add_tool("edit_file", "Surgical text replacement in a file",
    {"type": "object", "properties": {"path": {"type": "string"}, "old": {"type": "string"}, "new": {"type": "string"}}, "required": ["path", "old", "new"]}, edit_file)

server.add_tool("replace_text", "High-precision text replacement tool. Requires exact match of context.",
    {"type": "object", "properties": {"path": {"type": "string"}, "old_string": {"type": "string"}, "new_string": {"type": "string"}}, "required": ["path", "old_string", "new_string"]}, replace_text)

server.add_tool("get_file_info", "Get file metadata",
    {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}, get_file_info)

if __name__ == "__main__":
    server.run()
