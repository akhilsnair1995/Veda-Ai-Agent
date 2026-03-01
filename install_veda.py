# install_veda.py
import os
import sys
import platform
import subprocess
import subprocess
from pathlib import Path

def run_command(cmd, shell=False):
    print(f"Executing: {cmd}")
    try:
        subprocess.run(cmd, check=True, shell=shell)
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {e}")
        return False
    return True

def install():
    print("--- VEDA AI AGENT: UNIVERSAL INSTALLER ---")
    current_os = platform.system().lower()
    base_dir = Path(__file__).resolve().parent
    
    # 1. Create directory structure
    dirs = ["logs", "memory", "config", "notes", "persona/skills"]
    for d in dirs:
        (base_dir / d).mkdir(parents=True, exist_ok=True)
        print(f"✓ Directory created: {d}")

    # 2. Set up virtual environment
    venv_name = "venv_veda"
    venv_path = base_dir / venv_name
    
    if not venv_path.exists():
        print(f"Creating virtual environment in {venv_name}...")
        run_command([sys.executable, "-m", "venv", venv_name])
    
    # 3. Path to python/pip in venv
    if current_os == "windows":
        venv_python = venv_path / "Scripts" / "python.exe"
        venv_pip = venv_path / "Scripts" / "pip.exe"
    else:
        venv_python = venv_path / "bin" / "python"
        venv_pip = venv_path / "bin" / "pip"

    # 4. Install dependencies
    print("Installing dependencies...")
    # List core dependencies directly in case requirements.txt is missing
    deps = [
        "ollama", "rich", "click", "pyyaml", "requests", 
        "beautifulsoup4", "duckduckgo_search", "chromadb"
    ]
    
    run_command([str(venv_pip), "install", "-U", "pip"])
    run_command([str(venv_pip), "install"] + deps)
    
    if (base_dir / "requirements.txt").exists():
        run_command([str(venv_pip), "install", "-r", "requirements.txt"])

    # 5. Create launch scripts
    if current_os == "windows":
        with open(base_dir / "launch_veda.bat", "w") as f:
            f.write(f"@echo off
"{venv_python}" chat.py %*
")
        print("✓ Created launch_veda.bat")
    else:
        launch_sh = base_dir / "launch_veda.sh"
        with open(launch_sh, "w") as f:
            f.write(f"#!/bin/bash
"{venv_python}" chat.py "$@"
")
        run_command(["chmod", "+x", str(launch_sh)])
        print("✓ Created launch_veda.sh")

    print("
--- INSTALLATION COMPLETE ---")
    print("To start Veda:")
    if current_os == "windows":
        print("Run: ./launch_veda.bat")
    else:
        print("Run: ./launch_veda.sh")
    
    print("
Make sure you have Ollama installed and running (https://ollama.com)")

if __name__ == "__main__":
    install()
