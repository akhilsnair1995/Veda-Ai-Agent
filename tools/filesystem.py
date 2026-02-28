# tools/filesystem.py
# Gives the chatbot the ability to read and write files on your system.

from pathlib import Path
import os


def read_file(filepath: str) -> str:
    """
    Read the contents of a file.
    
    Example: read_file("~/Documents/myproject/main.py")
    """
    try:
        path = Path(filepath).expanduser().resolve()
        if not path.exists():
            return f"Error: File not found at {filepath}"
        if not path.is_file():
            return f"Error: {filepath} is not a file"
        content = path.read_text(encoding="utf-8")
        return f"Contents of {filepath}:\n\n{content}"
    except Exception as e:
        return f"Could not read file: {e}"


def write_file(filepath: str, content: str) -> str:
    """
    Write content to a file. Creates the file if it doesn't exist.
    Creates parent directories if they don't exist.
    
    Example: write_file("~/notes/todo.txt", "1. Buy groceries\n2. Call doctor")
    """
    try:
        path = Path(filepath).expanduser().resolve()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return f"Successfully wrote {len(content)} characters to {filepath}"
    except Exception as e:
        return f"Could not write file: {e}"


def list_files(directory: str = "/mnt/c/Users/akhil", pattern: str = "*") -> str:
    """
    List files in a directory.
    
    Example: list_files("~/Documents", "*.py")
    """
    try:
        path = Path(directory).expanduser().resolve()
        if not path.exists():
            return f"Directory not found: {directory}"

        files = list(path.glob(pattern))
        if not files:
            return f"No files matching '{pattern}' in {directory}"

        file_list = []
        for f in sorted(files)[:50]:  # Limit to 50 results
            size = f.stat().st_size if f.is_file() else 0
            kind = "dir" if f.is_dir() else "file"
            file_list.append(f"[{kind}] {f.name} ({size} bytes)" if f.is_file() else f"[{kind}] {f.name}/")

        return f"Contents of {directory}:\n" + "\n".join(file_list)
    except Exception as e:
        return f"Could not list directory: {e}"


def append_to_file(filepath: str, content: str) -> str:
    """
    Add content to the end of an existing file.
    
    Example: append_to_file("~/notes/diary.txt", "\nToday I built an AI!")
    """
    try:
        path = Path(filepath).expanduser().resolve()
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            f.write(content)
        return f"Appended content to {filepath}"
    except Exception as e:
        return f"Could not append to file: {e}"
