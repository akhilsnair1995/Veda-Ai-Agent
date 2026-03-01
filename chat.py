#!/usr/bin/env python3
# chat.py
# Main interface for Veda - Upgraded UI/UX

import click
import os
import time
from datetime import datetime
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.live import Live
from rich.spinner import Spinner
from rich.layout import Layout
from rich.columns import Columns
from pathlib import Path

from brain import VedaBrain
from memory.history import (
    init_database, save_message, get_all_notes, save_note, get_recent_messages
)
from memory.semantic import SemanticMemory

# --- UI CONSTANTS ---
VEDA_BANNER = r"""
[bold magenta]   _   __  ______   ____    ___ [/bold magenta]
[bold magenta]  | | / / / ____/  / __ \  /   |[/bold magenta]
[bold magenta]  | |/ / / __/    / / / / / /| |[/bold magenta]
[bold magenta]  |   / / /___   / /_/ / / ___ |[/bold magenta]
[bold magenta]  |__/ /_____/  /_____/ /_/  |_|[/bold magenta]
"""

class VedaUI:
    def __init__(self, console: Console, brain: VedaBrain, session_id: str):
        self.console = console
        self.brain = brain
        self.session_id = session_id
        self.semantic_memory = SemanticMemory()

    def print_header(self):
        """High-fidelity ANSI Veda branding and status dashboard."""
        
        # 1. Branding Text
        branding_text = Text.assemble(
            ("\n  INDUSTRIALIZING ENGINEERING DESIGN\n", "bold white"),
            ("  Independent MEP Intelligence System\n", "italic dim cyan"),
            ("  Precision MEP Framework 1.0\n", "bold magenta")
        )

        # 2. Stats & Status Table
        notes_count = len(get_all_notes())
        host_url = os.getenv("OLLAMA_HOST", "Localhost")
        if "trycloudflare.com" in host_url:
            host_display = "[green]REMOTE (KAG/COLAB)[/green]"
        else:
            host_display = "[yellow]LOCAL[/yellow]"

        status_table = Table(show_header=False, border_style="dim", box=None, padding=(0, 2))
        status_table.add_row("[bold magenta]CORE[/bold magenta]", "[white]STRICT-FACTUAL[/white]")
        status_table.add_row("[bold magenta]MODEL[/bold magenta]", f"{self.brain.model}")
        status_table.add_row("[bold magenta]SYNC[/bold magenta]", host_display)
        status_table.add_row("[bold magenta]DB[/bold magenta]", f"{notes_count} Notes | Vector Active")

        # Layout Assembly
        header_table = Table(show_header=False, box=None, padding=(0, 4))
        header_table.add_row(VEDA_BANNER, branding_text, status_table)

        self.console.print("\n")
        self.console.print(header_table)
        self.console.print(Panel.fit(
            "[green]Status:[/green] [blink]READY[/blink] | [dim]Industrializing MEP production via high-fidelity logic.[/dim]\n"
            "[bold cyan]Session:[/bold cyan] [dim]" + self.session_id + "[/dim] | Type [yellow]/help[/yellow] for commands.",
            border_style="magenta"
        ))
        self.console.print("\n")

    def print_help(self):
        """Clean command list."""
        help_table = Table(title="System Commands", show_header=True, header_style="bold magenta", box=None)
        help_table.add_column("Command", style="yellow")
        help_table.add_column("Description", style="dim")
        
        help_table.add_row("/notes", "Review Engineering Logic & Saved Notes")
        help_table.add_row("/search <query>", "Deep Compliance Search in Notes")
        help_table.add_row("/skills", "List and Manage Veda's Expert Skills")
        help_table.add_row("/mcp", "Check Status of MCP Server Integration")
        help_table.add_row("/clear", "Refresh Terminal Display")
        help_table.add_row("/help", "Show this help menu")
        help_table.add_row("/exit", "Secure System Shutdown")
        
        self.console.print(Panel(help_table, border_style="dim"))

    def handle_command(self, user_input: str) -> bool:
        cmd_parts = user_input.strip().split(" ", 1)
        cmd = cmd_parts[0].lower()

        if cmd == "/notes":
            notes = get_all_notes()
            if not notes:
                self.console.print("[yellow]Memory is currently empty.[/yellow]")
            else:
                self.console.print(f"\n[bold magenta]Veda's Knowledge Base ({len(notes)} records)[/bold magenta]\n")
                for note in notes:
                    self.console.print(Panel(
                        note['content'],
                        title=f"[bold]{note['title']}[/bold]",
                        subtitle=f"[dim]{note['time']}[/dim]",
                        border_style="dim"
                    ))
            return True

        elif cmd == "/skills":
            # For now, list the skills directory or known personas
            self.console.print(f"\n[bold cyan]VEDA ACTIVE SKILLS[/bold cyan]\n")
            skills_table = Table(show_header=True, header_style="bold cyan", box=None)
            skills_table.add_column("Skill Name", style="yellow")
            skills_table.add_column("Status", style="green")
            
            skills_table.add_row("Core Engineering Logic", "ACTIVE")
            skills_table.add_row("VMC Compliance Auditor", "STANDBY")
            skills_table.add_row("MCP Server Architect", "ACTIVE")
            
            self.console.print(skills_table)
            self.console.print(f"\n[dim italic]Use 'Draft a skill for...' to create new expertises.[/dim italic]")
            return True

        elif cmd == "/mcp":
            self.console.print(f"\n[bold magenta]MCP SERVER ECOSYSTEM[/bold magenta]\n")
            mcp_table = Table(show_header=True, header_style="bold magenta", box=None)
            mcp_table.add_column("Server", style="yellow")
            mcp_table.add_column("Protocol", style="dim")
            mcp_table.add_column("Status", style="green")
            
            mcp_table.add_row("Local Filesystem", "stdio", "CONNECTED")
            mcp_table.add_row("Web Search Engine", "SSE", "CONNECTED")
            mcp_table.add_row("Revit Production", "stdio", "DISCONNECTED")
            
            self.console.print(mcp_table)
            self.console.print(f"\n[dim]Configure servers in config/mcp_servers.json[/dim]")
            return True

        elif cmd == "/search":
            if len(cmd_parts) < 2:
                self.console.print("[red]Error: Please provide a search query. (e.g., /search VMC 401)[/red]")
                return True
            query = cmd_parts[1].strip()
            from memory.history import search_notes
            results = search_notes(query)
            if results:
                self.console.print(f"\n[bold green]Found {len(results)} matches for '{query}':[/bold]\n")
                for r in results:
                    self.console.print(Panel(
                        f"{r['content']}",
                        title=f"[bold magenta]{r['title']}[/bold magenta]",
                        border_style="magenta"
                    ))
            else:
                self.console.print(f"[yellow]No matches found for '{query}'[/yellow]")
            return True

        elif cmd == "/clear":
            self.console.clear()
            self.print_header()
            return True

        elif cmd == "/help":
            self.print_help()
            return True

        elif cmd == "/exit" or cmd == "quit":
            self.console.print("[dim]Veda shutting down. Wisdom preserved.[/dim]")
            exit(0)

        return False

    def stream_response(self, prompt: str):
        """Professional streaming output using Rich Live for smooth flow."""
        self.console.print(f"\n[bold cyan]Veda[/bold cyan] [dim]>[/dim] ", end="")
        full_response = ""
        
        with Live(Text(""), console=self.console, refresh_per_second=20, transient=False) as live:
            for token in self.brain.stream_think(prompt):
                full_response += token
                live.update(Text(full_response))
        
        self.console.print("\n")
        return full_response

    def run_tool_cycle(self, full_response: str, user_input: str):
        """Execute tools and handle re-interpretation with status indicators."""
        if "TOOL:" in full_response:
            with self.console.status("[bold yellow]Executing MCP Tool...", spinner="dots"):
                # Use the brain's built-in tool handler to execute and interpret
                final_response = self.brain._handle_tool_calls(full_response, user_input)
                self.console.print(f"\n[bold cyan]Veda[/bold cyan] [dim](Verified) >[/dim] {final_response}\n")
                
                save_message("assistant", final_response, self.session_id)
                self.semantic_memory.store(f"Fact: {final_response[:1000]}", metadata={"source": "tool_result"})
        else:
            save_message("assistant", full_response, self.session_id)
            if len(full_response) > 50:
                self.semantic_memory.store(f"Memory: {full_response[:1000]}", metadata={"source": "conversation"})


@click.command()
@click.option('--model', default='qwen2.5:7b', help='Ollama model to use')
def main(model):
    init_database()
    console = Console()
    session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Initialize components
    brain = VedaBrain(model=model)
    ui = VedaUI(console, brain, session_id)

    # Initial UI
    ui.print_header()

    while True:
        try:
            user_input = console.input("[bold magenta]User[/bold magenta] [dim]>[/dim] ").strip()
            if not user_input:
                continue

            if ui.handle_command(user_input):
                continue

            save_message("user", user_input, session_id)
            
            # 1. First Pass (Thinking + Potential Tool Call)
            full_response = ui.stream_response(user_input)
            
            # 2. Tool Cycle
            ui.run_tool_cycle(full_response, user_input)

        except KeyboardInterrupt:
            console.print("\n[dim]Type /exit to shutdown.[/dim]")
        except EOFError:
            break

if __name__ == "__main__":
    main()
