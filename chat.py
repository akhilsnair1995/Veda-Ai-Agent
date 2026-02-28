#!/usr/bin/env python3
# chat.py
# Main interface for Veda.

import click
from datetime import datetime
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from pathlib import Path

from brain import AIBrain
from tool_handler import detect_and_execute_tool
from memory.history import (
    init_database, save_message, get_all_notes, save_note
)
from memory.semantic import SemanticMemory

console = Console()
SESSION_ID = datetime.now().strftime("%Y%m%d_%H%M%S")


def print_welcome():
    """High-fidelity Veda branding and status dashboard."""
    from rich.table import Table
    from rich.columns import Columns
    
    # 1. Sophisticated Neem Leaf ASCII
    leaf_ascii = r"""
[bold green]      __[/bold green]
[bold green]  _  /  \  _ [/bold green]
[bold green] ( \/    \/ )[/bold green]
[bold green]  \ serrated / [/bold green]
[bold green]   \  leaf  /  [/bold green]
[bold green]    \    /   [/bold green]
[bold green]     \__/    [/bold green]
"""
    
    # 2. Branding Text
    branding_text = Text.assemble(
        ("\n  V  E  D  A\n", "bold white on magenta"),
        ("  Independent MEP Intelligence\n", "italic dim"),
        ("  Industrializing Engineering Design\n", "bold cyan")
    )

    # 3. Status Table
    status_table = Table(show_header=False, border_style="dim", box=None)
    status_table.add_row("[bold cyan]VERSION[/bold cyan]", "1.0.0-PRO")
    status_table.add_row("[bold cyan]MODEL[/bold cyan]", "Qwen 2.5 32B (Colab)")
    status_table.add_row("[bold cyan]RUNTIME[/bold cyan]", "100% Offline / Private")
    status_table.add_row("[bold cyan]MEMORY[/bold cyan]", "SQLite + ChromaDB Sync")

    # Layout Assembly
    header_table = Table(show_header=False, box=None, padding=(0, 2))
    header_table.add_row(leaf_ascii, branding_text, status_table)

    console.print("\n")
    console.print(header_table)
    console.print(Panel.fit(
        "[green]Available Modules:[/green]\n"
        "  [yellow]/notes[/yellow]     — Knowledge Base      [yellow]/search[/yellow]    — Deep Search\n"
        "  [yellow]/clear[/yellow]     — Reset Interface     [yellow]/exit[/yellow]      — Secure Shutdown\n\n"
        "[bold green]System Status:[/bold green] [blink]● ONLINE[/blink] | [dim]Wisdom logic verified.[/dim]",
        title="[bold white]VEDA CORE INTERFACE[/bold white]",
        border_style="magenta",
        subtitle="[dim]Session ID: " + SESSION_ID + "[/dim]"
    ))
    console.print("\n")


def handle_special_commands(user_input: str, brain: AIBrain) -> bool:
    cmd = user_input.strip().lower()

    if cmd == "/notes":
        notes = get_all_notes()
        if not notes:
            console.print("[yellow]Memory is currently empty.[/yellow]")
        else:
            console.print(f"\n[bold magenta]Veda's Knowledge Base ({len(notes)} records)[/bold magenta]\n")
            for note in notes:
                console.print(Panel(
                    note['content'],
                    title=f"[bold]{note['title']}[/bold]",
                    border_style="dim"
                ))
        return True

    elif cmd.startswith("/search "):
        query = user_input[8:].strip()
        from memory.history import search_notes
        results = search_notes(query)
        if results:
            console.print(f"\n[bold]Found {len(results)} matches for '{query}':[/bold]\n")
            for r in results:
                console.print(f"[magenta]{r['title']}[/magenta]: {r['content'][:200]}...")
        else:
            console.print(f"[yellow]No matches found for '{query}'[/yellow]")
        return True

    elif cmd == "/clear":
        console.clear()
        return True

    elif cmd == "/exit" or cmd == "quit":
        console.print("[dim]Veda shutting down. Wisdom preserved.[/dim]")
        exit(0)

    return False


@click.command()
@click.option('--model', default='qwen2.5:32b', help='Ollama model to use')
def main(model):
    init_database()
    brain = AIBrain(model=model)
    semantic_memory = SemanticMemory()

    print_welcome()
    console.print(f"[dim]Model: {model} | Session: {SESSION_ID}[/dim]\n")

    while True:
        try:
            user_input = console.input("[bold magenta]User >[/bold magenta] ").strip()
            if not user_input:
                continue

            if handle_special_commands(user_input, brain):
                continue

            save_message("user", user_input, SESSION_ID)

            console.print("[bold cyan]Veda:[/bold cyan] ", end="")
            full_response = ""
            for token in brain.stream_think(user_input):
                print(token, end="", flush=True)
                full_response += token
            print()

            tool_used, tool_result = detect_and_execute_tool(full_response)

            if tool_used:
                console.print(f"\n[dim yellow]Source Found. Analyzing data...[/dim yellow]")
                interpretation_prompt = (
                    f"I have successfully researched the following data from the web/system:\n\n"
                    f"{tool_result}\n\n"
                    f"Based ONLY on this data, provide a definitive, technical response. Cite the specific code section (e.g., VMC 401.4). If the data is incomplete, state what is missing."
                )

                console.print("[bold cyan]Veda:[/bold cyan] ", end="")
                final_response = ""
                for token in brain.stream_think(interpretation_prompt):
                    print(token, end="", flush=True)
                    final_response += token
                print()

                save_message("assistant", final_response, SESSION_ID)
                # Store ONLY the factual conclusion, not the prompt
                semantic_memory.store(f"Fact: {final_response[:1000]}", metadata={"source": "researched_fact"})
            else:
                save_message("assistant", full_response, SESSION_ID)
                if len(full_response) > 50:
                    semantic_memory.store(f"Memory: {full_response[:1000]}", metadata={"source": "conversation"})

            console.print()

        except KeyboardInterrupt:
            console.print("\n[dim]Type /exit to shutdown.[/dim]")
        except EOFError:
            break


if __name__ == "__main__":
    main()
