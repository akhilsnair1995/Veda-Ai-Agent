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
[bold green]   _   __  ______   ____    ___ [/bold green]
[bold green]  | | / / / ____/  / __ \  /   |[/bold green]
[bold yellow]  | |/ / / __/    / / / / / /| |[/bold yellow]
[bold #8B4513]  |   / / /___   / /_/ / / ___ |[/bold #8B4513]
[bold #5D4037]  |__/ /_____/  /_____/ /_/  |_|[/bold #5D4037]
"""

class VedaUI:
    def __init__(self, console: Console, brain: VedaBrain, session_id: str):
        self.console = console
        self.brain = brain
        self.session_id = session_id
        self.semantic_memory = SemanticMemory()

    def print_header(self):
        """High-fidelity ANSI Veda branding and status dashboard."""
        # Set Terminal Title
        if os.name == 'nt':
            os.system("title Veda🧠Ready")
        else:
            print("\033]2;Veda🧠Ready\007", end="", flush=True)
        
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

    def print_init_errors(self):
        """Report any initialization failures."""
        if self.brain.init_errors:
            self.console.print("\n[bold red]WARNING: Some components failed to initialize:[/bold red]")
            for err in self.brain.init_errors:
                self.console.print(f"[yellow]⚠ {err}[/yellow]")
            self.console.print("[dim]Veda is still operational, but some capabilities may be limited.[/dim]\n")

    def print_help(self):
        """Clean command list."""
        help_table = Table(title="System Commands", show_header=True, header_style="bold magenta", box=None)
        help_table.add_column("Command", style="yellow")
        help_table.add_column("Description", style="dim")
        
        help_table.add_row("/model <name>", "Switch underlying Ollama model")
        help_table.add_row("/notes", "Review Engineering Logic & Saved Notes")
        help_table.add_row("/search <query>", "Deep Compliance Search in Notes")
        help_table.add_row("/skills", "List and Manage Veda's Expert Skills")
        help_table.add_row("/mcp", "Check Status of MCP Server Integration")
        help_table.add_row("/reload", "Reconnect to Ollama (refreshes host URL)")
        help_table.add_row("/evolve", "Run proactive gap analysis and auto-generate skills")
        help_table.add_row("/clear", "Refresh Terminal Display")
        help_table.add_row("/help", "Show this help menu")
        help_table.add_row("/exit", "Secure System Shutdown")
        
        self.console.print(Panel(help_table, border_style="dim"))

    def handle_command(self, user_input: str) -> bool:
        cmd_parts = user_input.strip().split(" ", 1)
        cmd = cmd_parts[0].lower()

        if cmd == "/evolve":
            self.console.print("[dim]Launching Proactive Evolution Engine...[/dim]")
            try:
                # We import and run it here to keep chat.py clean
                from proactive_evolution import run_evolution
                run_evolution()
            except Exception as e:
                self.console.print(f"[red]Evolution engine error: {e}[/red]")
            return True

        if cmd == "/reload":
            self.console.print("[dim]Refreshing connection to Ollama...[/dim]")
            # Re-fetch host and recreate client
            self.brain.client = ollama.Client(host=self.brain._get_host())
            self.console.print("[bold green]✓ Connection re-established.[/bold green]")
            return True

        if cmd == "/model":
            try:
                models_resp = self.brain.client.list()
                # Handle different ollama-python library versions
                models = models_resp.get('models', []) if isinstance(models_resp, dict) else models_resp.models
                
                if not models:
                    self.console.print("[yellow]No models found in Ollama.[/yellow]")
                    return True

                table = Table(title="Available Ollama Models", show_header=True, header_style="bold magenta")
                table.add_column("#", style="dim", width=4)
                table.add_column("Model Name", style="yellow")
                table.add_column("Size", style="green")

                for i, m in enumerate(models, 1):
                    # Handle different object types from ollama list
                    name = m.get('name') if isinstance(m, dict) else m.model
                    size_bytes = m.get('size') if isinstance(m, dict) else m.size
                    size_gb = f"{size_bytes / (1024**3):.2f} GB"
                    table.add_row(str(i), name, size_gb)

                self.console.print(table)
                choice = self.console.input("[bold cyan]Select model # (or press Enter to cancel): [/bold cyan]").strip()
                
                if choice.isdigit() and 1 <= int(choice) <= len(models):
                    selected = models[int(choice)-1]
                    new_model = selected.get('name') if isinstance(selected, dict) else selected.model
                    self.console.print(f"[bold yellow]Switching to {new_model}...[/bold yellow]")
                    self.brain.model = new_model
                    self.console.print(f"[bold green]✓ Model active.[/bold green]")
                return True
            except Exception as e:
                self.console.print(f"[red]Error listing models: {e}[/red]")
                return True

        elif cmd == "/notes":
            notes = get_all_notes()
            if not notes:
                self.console.print("[yellow]No notes found in memory.[/yellow]")
                return True
            
            table = Table(title="Veda's Engineering Notes", show_header=True, header_style="bold magenta")
            table.add_column("#", style="dim", width=4)
            table.add_column("Title", style="yellow")
            table.add_column("Created", style="dim")

            for i, n in enumerate(notes, 1):
                table.add_row(str(i), n['title'], n['time'])
            
            self.console.print(table)
            choice = self.console.input("[bold cyan]Select note # to read (or Enter to cancel): [/bold cyan]").strip()
            
            if choice.isdigit() and 1 <= int(choice) <= len(notes):
                selected = notes[int(choice)-1]
                self.console.print(Panel(
                    selected['content'],
                    title=f"[bold]{selected['title']}[/bold]",
                    border_style="magenta"
                ))
            return True

        elif cmd == "/skills":
            skills = self.brain.skill_registry.skills
            table = Table(title="Veda's Active Expertise", show_header=True, header_style="bold cyan")
            table.add_column("#", style="dim", width=4)
            table.add_column("Expertise", style="yellow")
            table.add_column("Domain", style="dim")

            for i, (name, skill) in enumerate(skills.items(), 1):
                table.add_row(str(i), skill.metadata.name, skill.metadata.domain)
            
            self.console.print(table)
            choice = self.console.input("[bold cyan]Select # for details (or Enter to cancel): [/bold cyan]").strip()
            
            if choice.isdigit() and 1 <= int(choice) <= len(skills):
                skill_name = list(skills.keys())[int(choice)-1]
                skill = skills[skill_name]
                self.console.print(Panel(
                    f"[bold yellow]Description:[/bold yellow] {skill.metadata.description}\n"
                    f"[bold yellow]Triggers:[/bold yellow] {', '.join(skill.metadata.trigger_keywords)}",
                    title=f"[bold cyan]{skill.metadata.name}[/bold cyan]",
                    border_style="cyan"
                ))
            return True

        elif cmd == "/mcp":
            servers = self.brain.mcp_manager.clients
            table = Table(title="Connected MCP Servers", show_header=True, header_style="bold magenta")
            table.add_column("#", style="dim", width=4)
            table.add_column("Server", style="yellow")
            table.add_column("Tools", style="green")

            for i, name in enumerate(servers.keys(), 1):
                # Count tools for this server
                count = len([t for t, s in self.brain.mcp_manager.tool_routing.items() if s == name and "__" in t])
                table.add_row(str(i), name, str(count))
            
            self.console.print(table)
            choice = self.console.input("[bold cyan]Select server # to list tools (or Enter to cancel): [/bold cyan]").strip()
            
            if choice.isdigit() and 1 <= int(choice) <= len(servers):
                server_name = list(servers.keys())[int(choice)-1]
                tools = [t for t, s in self.brain.mcp_manager.tool_routing.items() if s == server_name and "__" in t]
                
                tool_table = Table(title=f"Tools for {server_name}", show_header=True)
                tool_table.add_column("Tool Name", style="yellow")
                tool_table.add_column("Description", style="dim")
                
                for t in tools:
                    schema = self.brain.mcp_manager.all_tools.get(t, {})
                    tool_table.add_row(t.replace(f"{server_name}__", ""), schema.get('description', ''))
                
                self.console.print(tool_table)
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
        
        # 1. Show Thinking Spinner while waiting for first token
        with self.console.status("[bold cyan]Thinking...", spinner="arc"):
            stream = self.brain.stream_think(prompt)
            try:
                # Get the first token to stop the spinner
                first_token = next(stream)
                full_response += first_token
            except StopIteration:
                return ""

        # 2. Transition to Live Streaming
        with Live(Text(full_response), console=self.console, refresh_per_second=20, transient=False) as live:
            for token in stream:
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

    # Clear screen before showing dashboard
    console.clear()

    # Initial UI
    ui.print_header()
    ui.print_init_errors()

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
