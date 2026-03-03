# mcp/servers/system_apps_server.py
import os
import sys
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR))
from mcp.server_base import MCPServer

server = MCPServer(name="system_apps", version="1.0.0")

def open_app(app_name: str) -> str:
    """Open a common Windows application (e.g., 'notepad', 'calc', 'explorer')."""
    try:
        # Check if it's a common alias
        aliases = {
            "notepad": "notepad.exe",
            "calculator": "calc.exe",
            "calc": "calc.exe",
            "explorer": "explorer.exe",
            "chrome": "chrome.exe",
            "edge": "msedge.exe",
            "word": "winword.exe",
            "excel": "excel.exe",
            "outlook": "outlook.exe",
            "powerpoint": "powerpnt.exe"
        }
        cmd = aliases.get(app_name.lower(), app_name)
        
        # Launch using start-process in powershell
        subprocess.Popen(["powershell.exe", "-NoProfile", "-Command", f"Start-Process {cmd}"], 
                         shell=True, 
                         stdout=subprocess.PIPE, 
                         stderr=subprocess.PIPE)
        return f"Successfully sent command to launch {app_name}."
    except Exception as e:
        return f"Error launching {app_name}: {e}"

def list_running_processes() -> str:
    """List current running processes with their names and IDs."""
    try:
        cmd = ["powershell.exe", "-NoProfile", "-Command", "Get-Process | Select-Object Name, Id, CPU | Sort-Object CPU -Descending | Select-Object -First 15 | ConvertTo-Json"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        return f"Top 15 CPU-intensive processes:
{result.stdout}"
    except Exception as e:
        return f"Error listing processes: {e}"

def kill_process(process_id: int) -> str:
    """Stop a running process by ID."""
    try:
        cmd = ["powershell.exe", "-NoProfile", "-Command", f"Stop-Process -Id {process_id} -Force"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            return f"Successfully killed process {process_id}."
        return f"Error: {result.stderr}"
    except Exception as e:
        return f"Error killing process: {e}"

def get_system_info() -> str:
    """Retrieve basic OS and hardware information."""
    try:
        cmd = ["powershell.exe", "-NoProfile", "-Command", "Get-ComputerInfo | Select-Object OsName, OsVersion, CsProcessors | ConvertTo-Json"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        return f"System Info:
{result.stdout}"
    except Exception as e:
        return f"Error getting system info: {e}"

def screen_capture(save_path: str = "screenshot.png") -> str:
    """Take a screenshot and save it to a file. Requires 'pillow' if implemented via python, or native ps command."""
    try:
        from PIL import ImageGrab
        p = Path(save_path).expanduser().resolve()
        p.parent.mkdir(parents=True, exist_ok=True)
        screenshot = ImageGrab.grab()
        screenshot.save(p)
        return f"Screenshot saved to {save_path}"
    except ImportError:
        return "Error: 'pillow' library required for screenshots. Run 'pip install pillow'."
    except Exception as e:
        return f"Error capturing screen: {e}"

server.add_tool("open_app", "Launch a Windows application by name or executable",
    {"type": "object", "properties": {"app_name": {"type": "string"}}, "required": ["app_name"]}, open_app)

server.add_tool("list_running_processes", "Show active system processes",
    {"type": "object", "properties": {}}, list_running_processes)

server.add_tool("kill_process", "Force stop a process by its PID",
    {"type": "object", "properties": {"process_id": {"type": "integer"}}, "required": ["process_id"]}, kill_process)

server.add_tool("get_system_info", "Get OS and hardware details",
    {"type": "object", "properties": {}}, get_system_info)

server.add_tool("screen_capture", "Take a screenshot of the primary display",
    {"type": "object", "properties": {"save_path": {"type": "string"}}}, screen_capture)

if __name__ == "__main__":
    server.run()
