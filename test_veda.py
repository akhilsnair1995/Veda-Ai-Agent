# test_veda.py
# Comprehensive Integration Test for Veda Architecture

import os
import sys
from pathlib import Path
from rich.console import Console

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from brain import VedaBrain
from mcp.server_manager import MCPServerManager
from skills.skill_registry import SkillRegistry

console = Console()

def run_tests():
    console.print("\n[bold cyan]=== VEDA INTEGRATION TESTS ===[/bold cyan]\n")
    
    # 1. Test Skill Registry
    console.print("[yellow]1. Testing Skill Registry...[/yellow]")
    registry = SkillRegistry()
    if len(registry.skills) > 0:
        console.print(f"[green]✓ Loaded {len(registry.skills)} skills[/green]")
    else:
        console.print("[red]✗ No skills loaded[/red]")
        
    # Check specific skill detection
    test_query = "Please review this python code: def foo(): pass"
    skill = registry.detect_skill(test_query, {})
    if skill and skill.metadata.name == "Code Review & Quality Auditor":
        console.print("[green]✓ Skill detection working[/green]")
    else:
        console.print(f"[red]✗ Skill detection failed. Got: {skill}[/red]")

    # 2. Test MCP Server Manager
    console.print("\n[yellow]2. Testing MCP Servers...[/yellow]")
    manager = MCPServerManager()
    manager.start_all()
    
    if len(manager.clients) > 0:
        console.print(f"[green]✓ Connected to {len(manager.clients)} MCP servers[/green]")
        console.print(f"[green]✓ Found {len(manager.all_tools)} tools total[/green]")
    else:
        console.print("[red]✗ No MCP servers connected[/red]")
        
    # Test a tool call
    if "filesystem__list_directory" in manager.all_tools:
        res = manager.call_tool("filesystem__list_directory", {"path": ".", "recursive": False, "pattern": "*"})
        if "Error" not in str(res):
            console.print("[green]✓ Tool execution successful (filesystem__list_directory)[/green]")
        else:
            console.print(f"[red]✗ Tool execution failed: {res}[/red]")
            
    manager.disconnect_all()
    
    # 3. Test Brain Initialization
    console.print("\n[yellow]3. Testing Brain...[/yellow]")
    try:
        brain = VedaBrain(model="qwen2.5:7b")
        console.print(f"[green]✓ Brain initialized with model {brain.model}[/green]")
        # To avoid actual slow LLM calls during automated test, we just check instantiation.
        # But we verify it loads memory and skills.
        if hasattr(brain, 'skill_registry') and hasattr(brain, 'mcp_manager'):
             console.print("[green]✓ Brain subcomponents loaded[/green]")
             
        brain.mcp_manager.disconnect_all()
    except Exception as e:
        console.print(f"[red]✗ Brain initialization failed: {e}[/red]")

    console.print("\n[bold cyan]=== TESTS COMPLETE ===[/bold cyan]\n")

if __name__ == "__main__":
    run_tests()
