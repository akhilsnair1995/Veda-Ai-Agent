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
    """Veda's welcome screen."""
    console.print(Panel.fit(
        "[bold magenta]V E D A[/bold magenta]\n"
        "[dim]Knowledge & Wisdom · 100% Offline · Linux[/dim]\n\n"
        "[green]Commands:[/green]\n"
        "  [yellow]/notes[/yellow]     — View stored memory\n"
        "  [yellow]/search[/yellow]    — Search notes\n"
        "  [yellow]/clear[/yellow]     — Clear screen\n"
        "  [yellow]/exit[/yellow]      — Shutdown\n\n"
        "[dim]Your independent intelligence is ready.[/dim]",
        title="[bold]Veda System Active[/bold]",
        border_style="magenta"
    ))


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
@click.option('--model', default='llama3.2:latest', help='Ollama model to use')
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
                console.print(f"\n[dim yellow]Executing tool and analyzing result...[/dim yellow]")
                interpretation_prompt = (
                    f"Result of tool execution:\n{tool_result}\n\n"
                    f"Analyze and present this information to the owner as Veda."
                )

                console.print("[bold cyan]Veda:[/bold cyan] ", end="")
                final_response = ""
                for token in brain.stream_think(interpretation_prompt):
                    print(token, end="", flush=True)
                    final_response += token
                print()

                save_message("assistant", final_response, SESSION_ID)
                semantic_memory.store(f"User: {user_input}\nVeda: {final_response[:500]}")
            else:
                save_message("assistant", full_response, SESSION_ID)
                if len(full_response) > 50:
                    semantic_memory.store(f"User: {user_input}\nVeda: {full_response[:500]}")

            console.print()

        except KeyboardInterrupt:
            console.print("\n[dim]Type /exit to shutdown.[/dim]")
        except EOFError:
            break


if __name__ == "__main__":
    main()
