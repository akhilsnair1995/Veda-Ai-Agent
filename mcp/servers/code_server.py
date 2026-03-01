# mcp/servers/code_server.py
import sys
import os
import subprocess
import tempfile
import ast
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR))
from mcp.server_base import MCPServer

server = MCPServer(name="code", version="1.0.0")

def run_python(code: str, timeout: int = 10) -> str:
    # Sandboxed execution using a temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(code)
        temp_path = f.name
    
    try:
        result = subprocess.run(
            [sys.executable, temp_path],
            capture_output=True,
            text=True,
            timeout=timeout
        )
        output = f"STDOUT:
{result.stdout}
STDERR:
{result.stderr}"
    except subprocess.TimeoutExpired:
        output = f"Error: Execution timed out after {timeout} seconds."
    except Exception as e:
        output = f"Execution error: {e}"
    finally:
        os.unlink(temp_path)
    
    return output

def run_shell(command: str, timeout: int = 10, confirm: bool = False) -> str:
    if not confirm:
        return "Must provide confirm=True to run shell commands."
    
    # Block obviously dangerous commands
    dangerous = ["rm -rf /", "mkfs", "dd if=", "> /dev/sda"]
    for d in dangerous:
        if d in command:
            return "Command blocked by security policy."

    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return f"Exit Code: {result.returncode}
STDOUT:
{result.stdout}
STDERR:
{result.stderr}"
    except subprocess.TimeoutExpired:
        return "Error: Shell command timed out."
    except Exception as e:
        return f"Shell error: {e}"

def lint_python(filepath: str) -> str:
    try:
        # Check if flake8 is installed
        result = subprocess.run(["flake8", filepath], capture_output=True, text=True)
        if result.returncode == 0:
            return "No linting errors found."
        return result.stdout
    except Exception:
        # Fallback to simple py_compile
        try:
            import py_compile
            py_compile.compile(filepath, doraise=True)
            return "Syntax OK."
        except py_compile.PyCompileError as e:
            return f"Syntax Error: {e}"

def format_python(filepath: str) -> str:
    try:
        result = subprocess.run(["black", filepath], capture_output=True, text=True)
        return f"Formatter output:
{result.stderr}" # black logs to stderr
    except Exception as e:
        return f"Format error (ensure black is installed): {e}"

def analyze_file(filepath: str) -> str:
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            tree = ast.parse(f.read(), filename=filepath)
        
        functions = [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
        classes = [node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
        imports = [node.names[0].name for node in ast.walk(tree) if isinstance(node, ast.Import)]
        from_imports = [f"{node.module} ({node.names[0].name})" for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)]
        
        return f"File: {filepath}
Classes: {', '.join(classes)}
Functions: {', '.join(functions)}
Imports: {', '.join(imports + from_imports)}"
    except Exception as e:
        return f"Analysis error: {e}"

def search_code(directory: str, query: str, language: str = "*") -> str:
    try:
        # A simple recursive search
        p = Path(directory)
        matches = []
        for path in p.rglob(f"*.{language}" if language != "*" else "*.*"):
            if path.is_file() and not path.name.startswith("."):
                try:
                    content = path.read_text(encoding='utf-8')
                    if query in content:
                        # Extract the line
                        for i, line in enumerate(content.splitlines()):
                            if query in line:
                                matches.append(f"{path}:{i+1} - {line.strip()}")
                except UnicodeDecodeError:
                    pass
        return "
".join(matches[:50]) if matches else "No matches found."
    except Exception as e:
        return f"Search error: {e}"

def git_status(repo_path: str) -> str:
    return run_shell(f"git -C {repo_path} status --short", confirm=True)

def git_log(repo_path: str, limit: int = 5) -> str:
    return run_shell(f"git -C {repo_path} log -n {limit} --oneline", confirm=True)

def git_diff(repo_path: str) -> str:
    return run_shell(f"git -C {repo_path} diff", confirm=True)

server.add_tool("run_python", "Execute python code safely",
    {"type": "object", "properties": {"code": {"type": "string"}, "timeout": {"type": "integer"}}, "required": ["code"]}, run_python)
server.add_tool("run_shell", "Run a shell command",
    {"type": "object", "properties": {"command": {"type": "string"}, "timeout": {"type": "integer"}, "confirm": {"type": "boolean"}}, "required": ["command", "confirm"]}, run_shell)
server.add_tool("lint_python", "Lint a python file",
    {"type": "object", "properties": {"filepath": {"type": "string"}}, "required": ["filepath"]}, lint_python)
server.add_tool("format_python", "Format a python file using Black",
    {"type": "object", "properties": {"filepath": {"type": "string"}}, "required": ["filepath"]}, format_python)
server.add_tool("analyze_file", "AST analysis of a Python file",
    {"type": "object", "properties": {"filepath": {"type": "string"}}, "required": ["filepath"]}, analyze_file)
server.add_tool("search_code", "Search code in a directory",
    {"type": "object", "properties": {"directory": {"type": "string"}, "query": {"type": "string"}, "language": {"type": "string"}}, "required": ["directory", "query"]}, search_code)
server.add_tool("git_status", "Get git status",
    {"type": "object", "properties": {"repo_path": {"type": "string"}}, "required": ["repo_path"]}, git_status)
server.add_tool("git_log", "Get recent git commits",
    {"type": "object", "properties": {"repo_path": {"type": "string"}, "limit": {"type": "integer"}}, "required": ["repo_path"]}, git_log)
server.add_tool("git_diff", "Get git diff",
    {"type": "object", "properties": {"repo_path": {"type": "string"}}, "required": ["repo_path"]}, git_diff)

if __name__ == "__main__":
    server.run()
