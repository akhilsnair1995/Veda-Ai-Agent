# proactive_evolution.py
import sys
import time
from pathlib import Path
from rich.console import Console
from rich.panel import Panel

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from brain import VedaBrain
from memory.history import get_recent_messages

console = Console()

def run_evolution():
    console.print(Panel.fit("[bold magenta]Veda Proactive Evolution Engine[/bold magenta]\n[dim]Analyzing recent conversations to identify knowledge gaps and generate new skills...[/dim]"))
    
    # 1. Fetch recent history
    recent = get_recent_messages(limit=50)
    if not recent:
        console.print("[yellow]Not enough conversation history to analyze.[/yellow]")
        return

    # Extract just the user queries to find patterns
    user_queries = [msg['content'] for msg in recent if msg['role'] == 'user']
    history_text = "\n".join(user_queries)

    # 2. Analyze for gaps using the LLM directly
    brain = VedaBrain()
    
    analysis_prompt = (
        "Analyze the following recent user queries. Identify ONE specific, recurring engineering or software topic "
        "that the user frequently asks about, which indicates a gap in my specialized skills. "
        "Respond ONLY with the name of the topic and a 1-sentence description of the required skill. "
        "If there is no clear recurring pattern, respond with 'NO_GAP_FOUND'.\n\n"
        "RECENT QUERIES:\n" + history_text
    )
    
    console.print("[cyan]Analyzing conversation history for patterns...[/cyan]")
    analysis_result = brain.think(analysis_prompt)
    
    if "NO_GAP_FOUND" in analysis_result.upper():
        console.print("[green]No significant skill gaps detected in recent history. Evolution paused.[/green]")
        return
        
    console.print(f"\n[bold yellow]Identified Gap:[/bold yellow]\n{analysis_result}\n")
    
    # 3. Trigger Self-Improvement
    console.print("[cyan]Initiating Autonomous Skill Generation...[/cyan]")
    evolution_prompt = (
        f"Based on the following identified knowledge gap, please use your self-evolution protocol "
        f"to write a new Python skill file to handle this topic.\n\nGAP: {analysis_result}"
    )
    
    # We pass this to the brain, which should trigger the SelfImprovementSkill automatically 
    # because of the trigger keywords in its metadata, or we can just call it directly.
    # Let's call the skill directly for guaranteed execution.
    skill = brain.skill_registry.get_skill("Veda Self-Evolution Core")
    if not skill:
        console.print("[red]Error: Self-Evolution Core skill not found.[/red]")
        return
        
    result = skill.execute(evolution_prompt, {}, brain)
    
    if result.success:
        console.print(Panel(result.output, title="[bold green]Evolution Successful[/bold green]", border_style="green"))
    else:
        console.print(f"[red]Evolution Failed: {result.output}[/red]")

if __name__ == '__main__':
    run_evolution()
