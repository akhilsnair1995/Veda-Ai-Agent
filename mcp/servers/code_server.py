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
    env_ws = os.getenv("VEDA_WORKSPACE")
    if env_ws:
        p = Path(env_ws).expanduser().resolve()
        if p.is_dir():
            return p
    default_ws = (BASE_DIR / "workspace").resolve()
    default_ws.mkdir(parents=True, exist_ok=True)
    return default_ws

def run_python(code: str = None, timeout: int = 30, python_code: str = None, file_path: str = None, path: str = None, **kwargs) -> str:
    """Execute python code. Can take raw code or a path to a .py file."""
    code = code or python_code
    target_path = file_path or path
    
    # If a path is provided, read the code from the file
    if target_path:
        try:
            # Check relative to workspace if not absolute
            p = Path(target_path).expanduser()
            if not p.is_absolute():
                p = _get_workspace() / p
            
            if p.exists() and p.is_file():
                code = p.read_text(encoding="utf-8")
            else:
                return f"Error: File not found at {target_path}"
        except Exception as e:
            return f"Error reading script file: {e}"

    if not code:
        return "Error: No code or file_path provided."

    # Automatic Plotting Fix
    if "plt.show()" in code:
        if "plt.savefig" not in code:
            code = code.replace("plt.show()", "plt.savefig('auto_generated_plot.png')")
        else:
            code = code.replace("plt.show()", "# plt.show() removed for headless execution")

    # Sandboxed execution
    fd, temp_path = tempfile.mkstemp(suffix='.py')
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            f.write(code)
        
        result = subprocess.run(
            [sys.executable, temp_path],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(_get_workspace())
        )
        return f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
    except subprocess.TimeoutExpired:
        return f"Error: Execution timed out after {timeout} seconds."
    except Exception as e:
        return f"Execution error: {e}"
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)

def run_shell(command: str, timeout: int = 10, confirm: bool = True, **kwargs) -> str:
    if not confirm:
        return "Command cancelled by user (confirm=False)."
    
    # Block obviously dangerous commands
    dangerous = ["rm -rf /", "mkfs", "dd if=", "> /dev/sda"]
    for d in dangerous:
        if d in command:
            return "Command blocked by security policy."

    try:
        # Use PowerShell on Windows for better compatibility
        shell_cmd = ["powershell.exe", "-NoProfile", "-Command", command] if os.name == 'nt' else command
        
        result = subprocess.run(
            shell_cmd,
            shell=(os.name != 'nt'),
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(_get_workspace())
        )
        return f"Exit Code: {result.returncode}\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
    except subprocess.TimeoutExpired:
        return "Error: Shell command timed out."
    except Exception as e:
        return f"Shell error: {e}"

def lint_python(filepath: str = None, path: str = None, file_path: str = None, **kwargs) -> str:
    target = filepath or path or file_path
    if not target:
        return "Error: No filepath provided."
    try:
        result = subprocess.run(["flake8", target], capture_output=True, text=True)
        if result.returncode == 0:
            return "No linting errors found."
        return result.stdout
    except Exception:
        try:
            import py_compile
            py_compile.compile(target, doraise=True)
            return "Syntax OK."
        except py_compile.PyCompileError as e:
            return f"Syntax Error: {e}"

def format_python(filepath: str = None, path: str = None, file_path: str = None, **kwargs) -> str:
    target = filepath or path or file_path
    if not target:
        return "Error: No filepath provided."
    try:
        result = subprocess.run(["black", target], capture_output=True, text=True)
        return f"Formatter output:\n{result.stderr}"
    except Exception as e:
        return f"Format error (ensure black is installed): {e}"

def analyze_file(filepath: str = None, path: str = None, file_path: str = None, **kwargs) -> str:
    target = filepath or path or file_path
    if not target:
        return "Error: No filepath provided."
    
    if os.path.isdir(target):
        return f"Target '{target}' is a directory. Use 'list_directory' or a shell command to see its contents."

    try:
        with open(target, 'r', encoding='utf-8') as f:
            tree = ast.parse(f.read(), filename=target)
        
        functions = [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
        classes = [node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
        imports = [node.names[0].name for node in ast.walk(tree) if isinstance(node, ast.Import)]
        from_imports = [f"{node.module} ({node.names[0].name})" for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)]
        
        return f"File: {target}\nClasses: {', '.join(classes)}\nFunctions: {', '.join(functions)}\nImports: {', '.join(imports + from_imports)}"
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
        return "\n".join(matches[:50]) if matches else "No matches found."
    except Exception as e:
        return f"Search error: {e}"

def git_status(repo_path: str = ".") -> str:
    return run_shell(f"git -C {repo_path} status --short", confirm=True)

def git_log(repo_path: str = ".", limit: int = 5) -> str:
    return run_shell(f"git -C {repo_path} log -n {limit} --oneline", confirm=True)

def git_diff(repo_path: str = ".") -> str:
    return run_shell(f"git -C {repo_path} diff", confirm=True)

server.add_tool("run_python", "Execute python code safely",
    {"type": "object", "properties": {"code": {"type": "string"}, "timeout": {"type": "integer"}}, "required": ["code"]}, run_python)
server.add_tool("run_shell", "Run a shell command",
    {"type": "object", "properties": {"command": {"type": "string"}, "timeout": {"type": "integer"}, "confirm": {"type": "boolean"}}, "required": ["command"]}, run_shell)
server.add_tool("lint_python", "Lint a python file",
    {"type": "object", "properties": {"filepath": {"type": "string"}}, "required": ["filepath"]}, lint_python)
server.add_tool("format_python", "Format a python file using Black",
    {"type": "object", "properties": {"filepath": {"type": "string"}}, "required": ["filepath"]}, format_python)
server.add_tool("analyze_file", "AST analysis of a Python file",
    {"type": "object", "properties": {"filepath": {"type": "string"}}, "required": ["filepath"]}, analyze_file)
server.add_tool("search_code", "Search code in a directory",
    {"type": "object", "properties": {"directory": {"type": "string"}, "query": {"type": "string"}, "language": {"type": "string"}}, "required": ["directory", "query"]}, search_code)
server.add_tool("git_status", "Get git status",
    {"type": "object", "properties": {"repo_path": {"type": "string"}}}, git_status)
server.add_tool("git_log", "Get recent git commits",
    {"type": "object", "properties": {"repo_path": {"type": "string"}, "limit": {"type": "integer"}}}, git_log)
server.add_tool("git_diff", "Get git diff",
    {"type": "object", "properties": {"repo_path": {"type": "string"}}}, git_diff)

if __name__ == "__main__":
    server.run()
