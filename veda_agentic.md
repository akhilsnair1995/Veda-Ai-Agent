# VEDA AGENTIC SYSTEM
### Claude Code + Gemini CLI Level — Complete Build Document

---

## WHAT THIS BUILDS

Veda becomes a full agentic terminal assistant:
- Reads entire codebases, understands them before touching anything
- Writes and edits files surgically — specific lines, not full rewrites
- Runs code, catches errors, fixes them, runs again — autonomously
- Executes shell commands and understands their output
- Plans multi-step tasks and executes each step in sequence
- Researches anything — web search, reads full pages, synthesizes
- Tracks projects — remembers context across sessions permanently
- Asks before destructive actions only — never asks for simple reads/writes/runs
- Works on anything — coding, research, sysadmin, documents, automation

Architecture mirrors Claude Code:
1. User gives a task in plain English
2. Veda plans the steps needed
3. Veda executes step by step — reading, thinking, acting
4. Each tool result feeds back into the next decision
5. If something fails — diagnoses, adjusts, retries automatically
6. Reports what was done when complete

---

## FILE 1 — agent.py

```python
# ~/myai/agent.py
# Veda's agentic core — the engine that makes her like Claude Code.
# Plans tasks, executes steps, handles errors, reports results.

import re
import json
import subprocess
import sys
import shutil
from pathlib import Path
from dataclasses import dataclass, field
from typing import Generator
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.markdown import Markdown

import ollama
from memory.history import get_recent_messages, save_message
from memory.semantic import SemanticMemory

console = Console()

OLLAMA_HOST_FILE = Path.home() / "myai" / "config" / "colab_url.txt"
MAX_STEPS = 20
TIMEOUT = 30

# ─────────────────────────────────────────────────────────────
# SYSTEM PROMPT — COMPLETE AGENTIC IDENTITY
# ─────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are Veda — a fully autonomous local AI agent.
You run on Ollama on a Linux PC. You are NOT a cloud AI.
You are NOT ChatGPT, Claude, or Gemini.
You have DIRECT access to the local filesystem and shell.

YOUR IDENTITY:
- Brain: Local Ollama LLM (via Colab + Cloudflare tunnel)
- Memory: SQLite + ChromaDB — permanent, local
- Tools: Full filesystem, shell, Python runner, web search
- Autonomy: Act freely. Ask only before delete/overwrite.
- Mission: Complete any task fully and correctly.

HOW YOU WORK — THE AGENT LOOP:
For every task:
1. EXPLORE first — read files, list directories, understand context
2. PLAN — think through the steps needed
3. ACT — execute one tool at a time
4. OBSERVE — read the tool result carefully
5. CONTINUE — take the next logical step
6. DONE — when task is complete, report what was accomplished

TOOLS — USE EXACTLY THIS FORMAT:

Read a file:
ACTION: read_file
INPUT: {"path": "~/project/main.py"}

Write a new file:
ACTION: write_file
INPUT: {"path": "~/project/new.py", "content": "content here"}

Edit specific text in a file (preferred over full rewrite):
ACTION: edit_file
INPUT: {"path": "~/file.py", "old": "exact text to replace", "new": "replacement"}

List directory contents:
ACTION: list_files
INPUT: {"path": "~/project", "pattern": "*.py", "recursive": true}

Run a shell command:
ACTION: run_shell
INPUT: {"command": "python ~/project/app.py"}

Run Python code directly:
ACTION: run_python
INPUT: {"code": "import sys\nprint(sys.version)"}

Search the web:
ACTION: web_search
INPUT: {"query": "fastapi authentication tutorial"}

Fetch a full web page:
ACTION: fetch_url
INPUT: {"url": "https://fastapi.tiangolo.com/tutorial/"}

Search inside files:
ACTION: grep_files
INPUT: {"path": "~/project", "pattern": "def main", "extension": ".py"}

Get file/directory info:
ACTION: file_info
INPUT: {"path": "~/project"}

Create a directory:
ACTION: make_dir
INPUT: {"path": "~/project/new_folder"}

Move or rename:
ACTION: move_file
INPUT: {"from": "~/old.py", "to": "~/new.py"}

Delete (ALWAYS set confirmed: false first — Veda will ask owner):
ACTION: delete_file
INPUT: {"path": "~/file.txt", "confirmed": false}

Save to memory:
ACTION: save_memory
INPUT: {"title": "Project: Flask API", "content": "Working on auth system..."}

Search memory:
ACTION: search_memory
INPUT: {"query": "what project was I working on"}

Task complete:
DONE: Brief summary of exactly what was accomplished.

RULES — ALWAYS DO WITHOUT ASKING:
- Read any file relevant to the task
- List directories to understand structure
- Run shell commands that gather info (ls, cat, grep, git status, pip list)
- Write new files
- Edit existing files surgically
- Run code to test it
- Search the web
- Install packages with pip

RULES — ALWAYS ASK FIRST:
- Deleting files (use confirmed: false and explain what will be deleted)
- Completely overwriting a file (offer to show diff first)
- System-level changes that cannot be undone

CODING RULES:
- Before editing: always read the file first
- After running code: read the full output
- If code fails: read complete error, find root cause, fix root not symptom
- Never say "this should work" — run it and verify it does
- Fix errors autonomously — retry until passing or genuinely stuck

PROJECT RULES:
- Start every project task by exploring directory structure
- Read README, requirements.txt, package.json, or config files first
- After completing: summarize exactly what changed and what was tested

RESEARCH RULES:
- Search multiple queries for important questions
- Fetch and read full page content, not just snippets
- Synthesize across multiple sources
- Test code examples before presenting them

NEVER SAY:
- "I cannot access your filesystem" — YOU CAN
- "As an AI I don't have access to" — YOU DO
- "I cannot run code" — YOU CAN
- "You would need to do this yourself" — YOU DO IT
- "I am a language model without..." — WRONG. You are Veda. You have tools.

ANTI-HALLUCINATION:
- Never invent file contents — read them
- Never guess directory structure — list it
- Never claim code works — run it and verify
- When uncertain: say so, then search or read to find out"""


# ─────────────────────────────────────────────────────────────
# TOOL IMPLEMENTATIONS
# ─────────────────────────────────────────────────────────────

def _human_size(b: int) -> str:
    for u in ["B","KB","MB","GB"]:
        if b < 1024: return f"{b:.1f}{u}"
        b /= 1024
    return f"{b:.1f}TB"


def tool_read_file(path: str) -> str:
    try:
        p = Path(path).expanduser().resolve()
        if not p.exists(): return f"NOT FOUND: {path}"
        if p.is_dir(): return f"{path} is a directory. Use list_files."
        size = p.stat().st_size
        content = p.read_text(errors="replace")
        if size > 500_000:
            return f"[Large file — first 5000 chars]\n\n{content[:5000]}"
        return content
    except PermissionError: return f"PERMISSION DENIED: {path}"
    except Exception as e: return f"READ ERROR: {e}"


def tool_write_file(path: str, content: str) -> str:
    try:
        p = Path(path).expanduser().resolve()
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        lines = content.count('\n') + 1
        return f"WRITTEN: {path} ({lines} lines, {len(content)} chars)"
    except PermissionError: return f"PERMISSION DENIED: {path}"
    except Exception as e: return f"WRITE ERROR: {e}"


def tool_edit_file(path: str, old: str, new: str) -> str:
    try:
        p = Path(path).expanduser().resolve()
        if not p.exists(): return f"NOT FOUND: {path}"
        content = p.read_text(encoding="utf-8")
        if old not in content:
            similar = [l.strip() for l in content.split('\n') if old[:15].lower() in l.lower()]
            hint = "\nSimilar lines:\n" + "\n".join(similar[:3]) if similar else ""
            return f"TEXT NOT FOUND in {path}.\nSearched for:\n{old[:100]}{hint}"
        count = content.count(old)
        if count > 1:
            return f"FOUND {count} MATCHES — provide more context in 'old' to be specific."
        p.write_text(content.replace(old, new, 1), encoding="utf-8")
        return f"EDITED: {path} — replaced {len(old)} chars with {len(new)} chars."
    except Exception as e: return f"EDIT ERROR: {e}"


def tool_list_files(path: str = "~", pattern: str = "*",
                    recursive: bool = False) -> str:
    try:
        p = Path(path).expanduser().resolve()
        if not p.exists(): return f"NOT FOUND: {path}"
        items = sorted(p.rglob(pattern) if recursive else p.glob(pattern))[:300]
        if not items: return f"No items matching '{pattern}' in {path}"
        lines = [f"Contents of {p} ({len(items)} items):", ""]
        for item in items:
            try:
                rel = item.relative_to(p)
                if item.is_dir():
                    lines.append(f"📁 {rel}/")
                else:
                    lines.append(f"📄 {rel} ({_human_size(item.stat().st_size)})")
            except: lines.append(f"   {item.name}")
        return "\n".join(lines)
    except Exception as e: return f"LIST ERROR: {e}"


def tool_run_shell(command: str, timeout: int = TIMEOUT) -> str:
    blocked = ['rm -rf /','rm -rf ~','mkfs','dd if=/dev/zero',
               '> /dev/sd','chmod -R 777 /',':(){:|:&};:']
    for b in blocked:
        if b in command: return f"BLOCKED: dangerous pattern '{b}'"
    try:
        r = subprocess.run(command, shell=True, capture_output=True,
                           text=True, timeout=timeout, cwd=str(Path.home()))
        out = (r.stdout or "") + (r.stderr or "")
        if not out: out = f"Completed (exit {r.returncode})"
        return out[:5000]
    except subprocess.TimeoutExpired: return f"TIMEOUT after {timeout}s"
    except Exception as e: return f"SHELL ERROR: {e}"


def tool_run_python(code: str, timeout: int = 15) -> str:
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py',
                                     delete=False, encoding='utf-8') as f:
        f.write(code); tmp = f.name
    try:
        r = subprocess.run([sys.executable, tmp], capture_output=True,
                           text=True, timeout=timeout)
        stderr = r.stderr or ""
        # Auto-install missing packages
        if "ModuleNotFoundError" in stderr:
            m = re.search(r"No module named '([^']+)'", stderr)
            if m:
                pkg = m.group(1).split(".")[0]
                console.print(f"[dim]Installing {pkg}...[/dim]")
                subprocess.run([sys.executable,"-m","pip","install",pkg,"-q"],
                               capture_output=True)
                r = subprocess.run([sys.executable,tmp],capture_output=True,
                                   text=True,timeout=timeout)
                stderr = r.stderr or ""
        out = ""
        if r.stdout: out += f"OUTPUT:\n{r.stdout}"
        if stderr: out += f"\nSTDERR:\n{stderr}"
        return (out or "Ran successfully with no output.")[:5000]
    except subprocess.TimeoutExpired: return f"TIMEOUT after {timeout}s"
    except Exception as e: return f"PYTHON ERROR: {e}"
    finally: Path(tmp).unlink(missing_ok=True)


def tool_web_search(query: str) -> str:
    try:
        from duckduckgo_search import DDGS
        results = []
        with DDGS() as d:
            for r in d.text(query, max_results=6):
                results.append(f"**{r['title']}**\n{r['href']}\n{r['body']}")
        return f"Search: '{query}'\n\n" + "\n\n---\n\n".join(results) if results else "No results."
    except Exception as e: return f"SEARCH ERROR: {e}"


def tool_fetch_url(url: str) -> str:
    try:
        import requests
        from bs4 import BeautifulSoup
        r = requests.get(url, headers={"User-Agent":"Mozilla/5.0"}, timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")
        for t in soup(["script","style","nav","footer","header","aside"]):
            t.decompose()
        lines = [l for l in soup.get_text(separator="\n",strip=True).split('\n') if l.strip()]
        text = "\n".join(lines)
        return text[:6000] + ("\n[truncated]" if len(text)>6000 else "")
    except Exception as e: return f"FETCH ERROR: {e}"


def tool_grep_files(path: str, pattern: str, extension: str = "") -> str:
    try:
        p = Path(path).expanduser().resolve()
        results = []
        glob = f"**/*{extension}" if extension else "**/*"
        for f in p.glob(glob):
            if not f.is_file(): continue
            try:
                for i, line in enumerate(f.read_text(errors="replace").split('\n'), 1):
                    if pattern.lower() in line.lower():
                        results.append(f"{f.relative_to(p)}:{i}: {line.strip()}")
            except: pass
        if not results: return f"Pattern '{pattern}' not found in {path}"
        return f"{len(results)} matches:\n\n" + "\n".join(results[:80])
    except Exception as e: return f"GREP ERROR: {e}"


def tool_file_info(path: str) -> str:
    try:
        import datetime
        p = Path(path).expanduser().resolve()
        if not p.exists(): return f"NOT FOUND: {path}"
        st = p.stat()
        info = [
            f"Path: {p}",
            f"Type: {'Directory' if p.is_dir() else 'File'}",
            f"Size: {_human_size(st.st_size)}",
            f"Modified: {datetime.datetime.fromtimestamp(st.st_mtime).strftime('%Y-%m-%d %H:%M')}",
            f"Permissions: {oct(st.st_mode)[-3:]}",
        ]
        if p.is_dir():
            try: info.append(f"Contains: {len(list(p.iterdir()))} items")
            except: pass
        return "\n".join(info)
    except Exception as e: return f"INFO ERROR: {e}"


def tool_make_dir(path: str) -> str:
    try:
        Path(path).expanduser().resolve().mkdir(parents=True, exist_ok=True)
        return f"CREATED: {path}"
    except Exception as e: return f"MKDIR ERROR: {e}"


def tool_move_file(src: str, dst: str) -> str:
    try:
        s = Path(src).expanduser().resolve()
        d = Path(dst).expanduser().resolve()
        if not s.exists(): return f"SOURCE NOT FOUND: {src}"
        d.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(s), str(d))
        return f"MOVED: {src} → {dst}"
    except Exception as e: return f"MOVE ERROR: {e}"


def tool_delete_file(path: str, confirmed: bool = False) -> str:
    p = Path(path).expanduser().resolve()
    if not p.exists(): return f"NOT FOUND: {path}"
    if not confirmed:
        size = _human_size(p.stat().st_size) if p.is_file() else "directory"
        return (f"⚠ CONFIRMATION REQUIRED\n"
                f"  Path: {p}\n"
                f"  Size: {size}\n"
                f"  Type: {'file' if p.is_file() else 'directory'}\n\n"
                f"Tell Veda: 'yes delete {path}' to confirm.")
    try:
        if p.is_dir(): shutil.rmtree(str(p))
        else: p.unlink()
        return f"DELETED: {path}"
    except Exception as e: return f"DELETE ERROR: {e}"


def tool_save_memory(title: str, content: str) -> str:
    try:
        from memory.history import save_note
        return save_note(title, content)
    except Exception as e: return f"MEMORY ERROR: {e}"


def tool_search_memory(query: str) -> str:
    try:
        from memory.history import search_notes
        notes = search_notes(query)
        mem = SemanticMemory()
        semantic = mem.search(query, top_k=3)
        out = []
        if notes:
            out.append(f"NOTES ({len(notes)}):")
            for n in notes: out.append(f"  [{n['title']}]: {n['content'][:200]}")
        if semantic:
            out.append(f"\nSEMANTIC ({len(semantic)}):")
            for s in semantic: out.append(f"  {s[:200]}")
        return "\n".join(out) if out else f"Nothing found for: {query}"
    except Exception as e: return f"SEARCH ERROR: {e}"


# ─────────────────────────────────────────────────────────────
# TOOL ROUTER
# ─────────────────────────────────────────────────────────────

TOOLS = {
    "read_file":     lambda i: tool_read_file(i.get("path","")),
    "write_file":    lambda i: tool_write_file(i.get("path",""), i.get("content","")),
    "edit_file":     lambda i: tool_edit_file(i.get("path",""), i.get("old",""), i.get("new","")),
    "list_files":    lambda i: tool_list_files(i.get("path","~"), i.get("pattern","*"), i.get("recursive",False)),
    "run_shell":     lambda i: tool_run_shell(i.get("command",""), i.get("timeout",TIMEOUT)),
    "run_python":    lambda i: tool_run_python(i.get("code",""), i.get("timeout",15)),
    "web_search":    lambda i: tool_web_search(i.get("query","")),
    "fetch_url":     lambda i: tool_fetch_url(i.get("url","")),
    "grep_files":    lambda i: tool_grep_files(i.get("path","."), i.get("pattern",""), i.get("extension","")),
    "file_info":     lambda i: tool_file_info(i.get("path","")),
    "make_dir":      lambda i: tool_make_dir(i.get("path","")),
    "move_file":     lambda i: tool_move_file(i.get("from",""), i.get("to","")),
    "delete_file":   lambda i: tool_delete_file(i.get("path",""), i.get("confirmed",False)),
    "save_memory":   lambda i: tool_save_memory(i.get("title",""), i.get("content","")),
    "search_memory": lambda i: tool_search_memory(i.get("query","")),
}


def parse_action(response: str):
    """Parse ACTION+INPUT or DONE from LLM response."""
    if m := re.search(r'DONE:\s*(.+)', response, re.DOTALL):
        return "DONE", {"summary": m.group(1).strip()}
    if m := re.search(r'ACTION:\s*(\w+)', response):
        action = m.group(1).strip().lower()
        params = {}
        if pm := re.search(r'INPUT:\s*(\{.*?\})', response, re.DOTALL):
            try:
                params = json.loads(pm.group(1))
            except:
                try: params = json.loads(pm.group(1).replace("'",'"'))
                except: params = {}
        return action, params
    return None, None


def execute_action(action: str, params: dict) -> str:
    if action not in TOOLS:
        return f"UNKNOWN TOOL: '{action}'. Available: {list(TOOLS.keys())}"
    try:
        return TOOLS[action](params)
    except Exception as e:
        return f"TOOL FAILED ({action}): {e}"


# ─────────────────────────────────────────────────────────────
# VEDA AGENT
# ─────────────────────────────────────────────────────────────

class VedaAgent:
    def __init__(self, model: str = "llama3:8b"):
        self.model = model
        self.semantic_memory = SemanticMemory()
        self.client, self.host = self._connect()
        self._verify()

    def _connect(self):
        host = "http://localhost:11434"
        if OLLAMA_HOST_FILE.exists():
            h = OLLAMA_HOST_FILE.read_text().strip()
            if h: host = h
        return ollama.Client(host=host), host

    def _verify(self):
        try:
            models = self.client.list()
            available = [m['name'] for m in models.get('models',[])]
            console.print(f"[green]✓ Veda online — {self.host}[/green]")
            console.print(f"[dim]  Model: {self.model} | Available: {available}[/dim]")
        except Exception as e:
            console.print(f"[red]✗ Ollama unreachable: {e}[/red]")
            console.print("[yellow]  Run: setcolab <url>  or  ollama serve[/yellow]")

    def _llm(self, messages: list) -> str:
        try:
            r = self.client.chat(
                model=self.model, messages=messages,
                system=SYSTEM_PROMPT,
                options={"temperature": 0.1, "num_ctx": 8192}
            )
            return r['message']['content']
        except Exception as e:
            if "connection" in str(e).lower():
                return "✗ Lost connection. Run: setcolab <url>"
            return f"✗ LLM error: {e}"

    def _llm_stream(self, messages: list):
        try:
            stream = self.client.chat(
                model=self.model, messages=messages,
                stream=True, system=SYSTEM_PROMPT,
                options={"temperature": 0.1, "num_ctx": 8192}
            )
            for chunk in stream:
                yield chunk['message']['content']
        except Exception as e:
            yield f"\n✗ Error: {e}"

    def _context(self, query: str) -> str:
        retrieved = self.semantic_memory.search(query, top_k=4)
        if retrieved:
            return "MEMORY:\n" + "\n---\n".join(retrieved) + "\n\n"
        return ""

    def run_task(self, task: str) -> Generator:
        """
        The agentic loop.
        Yields display strings as Veda works through the task.
        """
        console.print(Panel(f"[bold cyan]Task:[/bold cyan] {task}", border_style="cyan"))

        ctx = self._context(task)
        messages = list(get_recent_messages(limit=6))
        messages.append({
            "role": "user",
            "content": f"{ctx}TASK: {task}\n\nBegin. Use your tools."
        })

        steps = []
        for step_num in range(1, MAX_STEPS + 1):
            console.print(f"[dim]  thinking (step {step_num})...[/dim]")
            response = self._llm(messages)

            if not response or response.startswith("✗"):
                yield f"\n{response}"
                break

            action, params = parse_action(response)

            # No tool — direct answer
            if action is None:
                yield response
                save_message("user", task, "agent")
                save_message("assistant", response, "agent")
                self.semantic_memory.store(f"Task: {task}\nResult: {response[:400]}")
                break

            # Task complete
            if action == "DONE":
                summary = params.get("summary","Task completed.")
                console.print(f"\n[bold green]✓ Done:[/bold green] {summary}")
                yield f"\n✅ **Done:** {summary}"
                self.semantic_memory.store(
                    f"Completed: {task}\nSteps:\n" + "\n".join(steps)
                )
                save_message("user", task, "agent")
                save_message("assistant", summary, "agent")
                break

            # Execute tool
            console.print(f"\n[bold cyan]⚡ {action}[/bold cyan] "
                          f"[dim]{json.dumps(params)[:80]}[/dim]")
            result = execute_action(action, params)

            preview = result[:150].replace('\n',' ')
            console.print(f"[dim green]  → {preview}[/dim green]")
            steps.append(f"Step {step_num}: {action} → {result[:80]}")

            messages.append({"role": "assistant", "content": response})
            messages.append({
                "role": "user",
                "content": (
                    f"RESULT of {action}:\n{result}\n\n"
                    f"Continue the task. Next step or DONE: <summary>."
                )
            })
        else:
            yield f"\n⚠ Step limit ({MAX_STEPS}) reached."

    def chat(self, message: str) -> Generator:
        """Simple streaming chat for questions."""
        ctx = self._context(message)
        messages = list(get_recent_messages(limit=8))
        messages.append({"role": "user", "content": f"{ctx}{message}"})

        full = ""
        for token in self._llm_stream(messages):
            full += token
            yield token

        save_message("user", message, "chat")
        save_message("assistant", full, "chat")
        if len(full) > 50:
            self.semantic_memory.store(f"Q: {message}\nA: {full[:400]}")

    def reload(self):
        self.client, self.host = self._connect()
        self._verify()
```

---

## FILE 2 — chat.py

```python
#!/usr/bin/env python3
# ~/myai/chat.py
# Veda's terminal interface — Claude Code / Gemini CLI style.

import click
import sys
from pathlib import Path
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from agent import VedaAgent, tool_list_files, tool_read_file, tool_run_shell
from memory.history import init_database, get_all_notes, search_notes

console = Console()

WELCOME = """[bold cyan]Veda[/bold cyan] — Local Agentic AI Assistant
[dim]Ollama · Local filesystem · Semi-autonomous[/dim]

[green]Just describe what you want done:[/green]
  [dim]"read my app.py and find bugs"[/dim]
  [dim]"build a script that monitors disk usage"[/dim]
  [dim]"research FastAPI auth and implement it in my project"[/dim]
  [dim]"fix the error in ~/project/main.py and test it"[/dim]
  [dim]"organize my Downloads folder by file type"[/dim]

[green]Commands:[/green]
  /files [path]      /read [path]      /run [cmd]
  /notes             /search [query]   /model
  /reload            /clear            /exit"""


# Keywords that trigger full agent loop vs simple chat
TASK_TRIGGERS = [
    "read","open","show","write","create","make","build","generate",
    "save","delete","remove","move","copy","rename","organize","find",
    "fix","debug","run","test","implement","refactor","add","update",
    "edit","change","install","script","code","function","search",
    "research","fetch","get","check","analyze","review","summarize",
    "monitor","setup","configure","automate","download","deploy",
    "grep","list files","what files","what's in","look at","explain my",
]


def is_task(msg: str) -> bool:
    m = msg.lower()
    return any(t in m for t in TASK_TRIGGERS)


def slash_command(cmd: str, agent: VedaAgent) -> bool:
    parts = cmd.strip().split(None, 1)
    c = parts[0].lower()
    arg = parts[1] if len(parts) > 1 else ""

    if c == "/files":
        console.print(tool_list_files(arg or "~"))
        return True

    if c == "/read":
        if not arg:
            console.print("[yellow]Usage: /read <path>[/yellow]")
            return True
        result = tool_read_file(arg)
        console.print(Markdown(f"```\n{result}\n```"))
        return True

    if c == "/run":
        if not arg:
            console.print("[yellow]Usage: /run <command>[/yellow]")
            return True
        confirm = input(f"Run '{arg}'? (yes/no): ").strip().lower()
        if confirm == "yes":
            console.print(tool_run_shell(arg))
        else:
            console.print("[dim]Cancelled.[/dim]")
        return True

    if c == "/notes":
        notes = get_all_notes()
        if not notes:
            console.print("[yellow]No notes yet.[/yellow]")
        for n in notes:
            console.print(Panel(n['content'],
                title=f"[bold]{n['title']}[/bold] [dim]{n['time'][:10]}[/dim]",
                border_style="dim"))
        return True

    if c == "/search":
        if not arg:
            console.print("[yellow]Usage: /search <query>[/yellow]")
            return True
        results = search_notes(arg)
        if results:
            for r in results:
                console.print(f"\n[cyan]{r['title']}[/cyan]: {r['content'][:300]}")
        else:
            console.print(f"[yellow]Nothing for '{arg}'[/yellow]")
        return True

    if c == "/model":
        console.print(f"[cyan]Model: {agent.model} | Host: {agent.host}[/cyan]")
        return True

    if c == "/reload":
        agent.reload()
        return True

    if c == "/clear":
        console.clear()
        return True

    if c in ("/exit", "/quit"):
        console.print("[dim]Goodbye.[/dim]")
        sys.exit(0)

    return False


@click.command()
@click.option('--model', default='llama3:8b', help='Ollama model')
@click.option('--file', '-f', 'filepath', default=None,
              help='Include a file as context for the task')
@click.argument('task', nargs=-1)
def main(model, filepath, task):
    """Veda — Local Agentic AI. Describe any task and she does it."""

    init_database()
    agent = VedaAgent(model=model)
    console.print(Panel(WELCOME, border_style="cyan"))

    # One-shot mode: veda "task here" or veda -f file.py "task"
    if task:
        full_task = " ".join(task)
        if filepath:
            content = tool_read_file(filepath)
            full_task = f"File: {filepath}\n\n{content}\n\nTask: {full_task}"
        console.print()
        for update in agent.run_task(full_task):
            if update:
                console.print(Markdown(update))
        return

    # Interactive mode
    file_ctx = filepath  # carry file context into first message

    while True:
        try:
            user_input = console.input("\n[bold green]You:[/bold green] ").strip()

            if not user_input:
                continue

            if user_input.lower() in ("exit","quit","bye"):
                console.print("[dim]Goodbye.[/dim]")
                break

            # Slash commands
            if user_input.startswith("/"):
                slash_command(user_input, agent)
                continue

            # Inject file context into first real message
            if file_ctx:
                content = tool_read_file(file_ctx)
                user_input = (f"File context ({file_ctx}):\n\n{content}\n\n"
                              f"Request: {user_input}")
                file_ctx = None

            # Task → agent loop | Question → chat
            if is_task(user_input):
                console.print()
                for update in agent.run_task(user_input):
                    if update:
                        console.print(Markdown(update))
            else:
                console.print("\n[bold blue]Veda:[/bold blue] ", end="")
                for token in agent.chat(user_input):
                    print(token, end="", flush=True)
                print()

        except KeyboardInterrupt:
            console.print("\n[dim]Tip: type exit to quit[/dim]")
        except EOFError:
            break
        except Exception as e:
            console.print(f"\n[red]Error: {e}[/red]")
            console.print("[dim]/reload to reconnect Ollama[/dim]")


if __name__ == "__main__":
    main()
```

---

## FILE 3 — memory/history.py

```python
# ~/myai/memory/history.py
import sqlite3
from datetime import datetime
from pathlib import Path

DB_FILE = Path.home() / "myai" / "memory" / "conversations.db"


def init_database():
    DB_FILE.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_FILE)
    conn.execute("""CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT, role TEXT, content TEXT, session_id TEXT)""")
    conn.execute("""CREATE TABLE IF NOT EXISTS notes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT, title TEXT, content TEXT, tags TEXT DEFAULT '')""")
    conn.commit()
    conn.close()


def save_message(role: str, content: str, session_id: str = "default"):
    conn = sqlite3.connect(DB_FILE)
    conn.execute(
        "INSERT INTO messages (timestamp,role,content,session_id) VALUES (?,?,?,?)",
        (datetime.now().isoformat(), role, content, session_id))
    conn.commit()
    conn.close()


def get_recent_messages(limit: int = 10) -> list:
    conn = sqlite3.connect(DB_FILE)
    rows = conn.execute(
        "SELECT role,content FROM messages ORDER BY timestamp DESC LIMIT ?",
        (limit,)).fetchall()
    conn.close()
    return [{"role": r[0], "content": r[1]} for r in reversed(rows)]


def save_note(title: str, content: str, tags: str = "") -> str:
    conn = sqlite3.connect(DB_FILE)
    conn.execute(
        "INSERT INTO notes (timestamp,title,content,tags) VALUES (?,?,?,?)",
        (datetime.now().isoformat(), title, content, tags))
    conn.commit()
    conn.close()
    return f"✓ Saved: '{title}'"


def get_all_notes() -> list:
    conn = sqlite3.connect(DB_FILE)
    rows = conn.execute(
        "SELECT title,content,tags,timestamp FROM notes ORDER BY timestamp DESC"
    ).fetchall()
    conn.close()
    return [{"title": r[0],"content": r[1],"tags": r[2],"time": r[3]} for r in rows]


def search_notes(query: str) -> list:
    conn = sqlite3.connect(DB_FILE)
    rows = conn.execute(
        "SELECT title,content,tags FROM notes WHERE content LIKE ? OR title LIKE ?",
        (f"%{query}%", f"%{query}%")).fetchall()
    conn.close()
    return [{"title": r[0],"content": r[1],"tags": r[2]} for r in rows]
```

---

## FILE 4 — memory/semantic.py

```python
# ~/myai/memory/semantic.py
import chromadb
from pathlib import Path

VECTOR_DB_PATH = str(Path.home() / "myai" / "memory" / "vectorstore")


class SemanticMemory:
    def __init__(self):
        self.client = chromadb.PersistentClient(path=VECTOR_DB_PATH)
        self.collection = self.client.get_or_create_collection(
            name="veda_memory",
            metadata={"hnsw:space": "cosine"})
        self._counter = self.collection.count()

    def store(self, text: str, metadata: dict = None):
        if not text or len(text.strip()) < 10:
            return
        self._counter += 1
        self.collection.add(
            documents=[text],
            metadatas=[metadata or {}],
            ids=[f"mem_{self._counter}"])

    def search(self, query: str, top_k: int = 4) -> list:
        n = self.collection.count()
        if n == 0:
            return []
        results = self.collection.query(
            query_texts=[query],
            n_results=min(top_k, n))
        return results['documents'][0] if results['documents'] else []
```

---

## FILE 5 — set_colab.sh

```bash
#!/bin/bash
# ~/myai/set_colab.sh
if [ -z "$1" ]; then
    echo "Paste Cloudflare tunnel URL:"
    read url
else
    url=$1
fi
url="${url%/}"
mkdir -p ~/myai/config
echo "$url" > ~/myai/config/colab_url.txt
echo "✓ Veda → $url"
echo -n "Testing... "
if curl -s --max-time 10 "$url/api/tags" > /dev/null 2>&1; then
    echo "✓ Connected! Run: veda"
else
    echo "✗ Unreachable. Check Colab is running."
fi
```

---

## FILE 6 — Google Colab Restart Cell

```python
# Paste as one cell — restarts everything after disconnection
import subprocess, time, re, requests

subprocess.Popen(["ollama","serve"],
                 stdout=subprocess.DEVNULL,
                 stderr=subprocess.DEVNULL)
time.sleep(5)

try:
    r = requests.get("http://localhost:11434/api/tags")
    print(f"✓ Ollama: {[m['name'] for m in r.json()['models']]}")
except:
    print("✗ Ollama not responding")

tunnel = subprocess.Popen(
    ["./cloudflared","tunnel","--url","http://localhost:11434"],
    stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

for _ in range(30):
    line = tunnel.stdout.readline().decode()
    m = re.search(r'https://[a-z0-9\-]+\.trycloudflare\.com', line)
    if m:
        url = m.group(0)
        print(f"\n{'='*50}")
        print(f"✓ Ready! Run on your Linux PC:")
        print(f'  setcolab "{url}"')
        print(f"  veda")
        print(f"{'='*50}")
        break
    time.sleep(1)
```

---

## SETUP — Run Once

```bash
#!/bin/bash
# ~/myai/setup.sh

set -e
echo "Setting up Veda agentic system..."

mkdir -p ~/myai/{memory,config,notes,logs}
touch ~/myai/memory/__init__.py

cd ~/myai
python3 -m venv venv
source venv/bin/activate

pip install -q ollama chromadb rich click requests \
            beautifulsoup4 duckduckgo-search pyyaml

chmod +x ~/myai/set_colab.sh

# Add shell aliases
grep -q 'alias veda=' ~/.bashrc || \
    echo 'alias veda="cd ~/myai && source venv/bin/activate && python chat.py"' >> ~/.bashrc
grep -q 'alias setcolab=' ~/.bashrc || \
    echo 'alias setcolab="~/myai/set_colab.sh"' >> ~/.bashrc

source ~/.bashrc
echo "✓ Done. Run: setcolab <url> then veda"
```

---

## VERIFICATION — Test Everything

```bash
cd ~/myai && source venv/bin/activate
python3 - << 'EOF'
from pathlib import Path
import ollama

host_file = Path.home() / "myai/config/colab_url.txt"
host = host_file.read_text().strip() if host_file.exists() else "http://localhost:11434"

# Test Ollama
try:
    c = ollama.Client(host=host)
    m = c.list()
    print(f"✓ Ollama at {host}")
    print(f"  Models: {[x['name'] for x in m.get('models',[])]}")
except Exception as e:
    print(f"✗ Ollama: {e}")

# Test memory
from memory.history import init_database, save_note, search_notes
init_database()
save_note("Verification","Setup test note")
r = search_notes("verification")
print(f"✓ SQLite memory ({len(r)} notes)")

# Test semantic memory
from memory.semantic import SemanticMemory
mem = SemanticMemory()
mem.store("Veda is a local autonomous AI agent")
r = mem.search("local AI")
print(f"✓ ChromaDB memory ({len(r)} results)")

# Test tools
from agent import tool_list_files, tool_read_file, tool_run_shell
r = tool_list_files("~")
print(f"✓ list_files working")
r = tool_run_shell("echo 'shell test'")
print(f"✓ run_shell working: {r.strip()}")

print("\n✓ All systems ready. Run: veda")
EOF
```

---

## HOW THE AGENT LOOP WORKS

```
You type: "read ~/myproject/app.py, find the bug, fix it and test"

Step 1 — Veda reads the file
  ACTION: read_file
  INPUT: {"path": "~/myproject/app.py"}
  → sees the actual code

Step 2 — Veda identifies the bug, makes surgical edit
  ACTION: edit_file
  INPUT: {"path": "~/myproject/app.py",
          "old": "return resutl",
          "new": "return result"}
  → file updated

Step 3 — Veda runs the fixed code
  ACTION: run_shell
  INPUT: {"command": "python ~/myproject/app.py"}
  → sees actual output

Step 4 — Tests pass
  DONE: Fixed typo on line 23 (resutl → result). Tests passing.

You see: ✅ Done: Fixed typo on line 23. Tests passing.
```

---

## EXAMPLE SESSIONS

```bash
# Launch interactive
veda

# One-shot tasks
veda "find all TODO comments in ~/myproject and list them"
veda "create a Flask hello world app in ~/demo"
veda "check disk usage and tell me the top 5 biggest folders"
veda "search for Python rate limiting best practices and summarize"
veda "read ~/myproject/requirements.txt and install everything missing"

# With file context
veda -f ~/myproject/app.py "review this code thoroughly"
veda -f ~/myproject/app.py "add proper error handling to every function"

# Inside interactive mode
You: what files are in my project?
You: read the main.py file
You: fix the import error on line 5
You: run the tests
You: search the web for how to add JWT auth to Flask
You: implement that in my current project
```

---

## GEMINI TRAINING PROMPT

Feed this to Gemini to generate Veda's knowledge about her own architecture:

```
Teach Veda — a fully local autonomous AI agent — everything about
how she works and how to be the best possible agentic assistant.

Veda's architecture:
- agent.py: agentic loop (plan → act → observe → iterate → done)
- chat.py: terminal interface with task detection
- Tools: read_file, write_file, edit_file, list_files, run_shell,
  run_python, web_search, fetch_url, grep_files, file_info,
  make_dir, move_file, delete_file, save_memory, search_memory
- Semi-autonomous: acts freely, asks only before delete/overwrite
- Memory: SQLite conversation history + ChromaDB semantic memory
- Brain: local Ollama LLM (llama3 or similar)

Teach Veda:

1. AGENTIC THINKING
   The right order is always: explore → understand → plan → act → verify
   Never skip explore. Never act on assumptions.
   After every tool result: re-read it, reflect, then decide next step.
   A task is done when verified working, not just written.

2. CODING AGENT BEHAVIOR
   - Read the file before editing it. Always.
   - Make surgical edits (edit_file) not full rewrites (write_file)
   - Run the code after every significant change
   - Read the full error message — first line and last line
   - Fix root cause — not the symptom
   - Test edge cases before declaring done
   - Use grep_files to understand a codebase before touching it

3. RESEARCH AGENT BEHAVIOR
   - Web search gives snippets — fetch_url gives full content
   - Search 2-3 different queries on the same topic
   - Read the actual documentation page, not just the description
   - When researching how to implement something: test it first
   - Synthesize from multiple sources — note where sources disagree

4. SYSTEM AGENT BEHAVIOR
   - Use run_shell to understand the system before modifying it
   - Always list_files before organizing anything
   - Always file_info before large operations
   - Never delete without showing the user what will be deleted
   - Prefer reversible operations (move) over irreversible (delete)

5. PROJECT MANAGER BEHAVIOR
   - Start every session: search_memory for current project context
   - End every significant task: save_memory with what was done and what is next
   - When starting a new project: explore full structure first
   - Keep a running project log in ~/myai/notes/

6. ERROR RECOVERY
   - If a tool returns an error: read the error carefully
   - Try the simplest fix first
   - If still failing: search the web for the error message
   - Never repeat the exact same failing approach
   - If completely stuck: report clearly what was tried and what failed

Write Veda's complete updated SYSTEM_PROMPT encoding all of the above.
Make her incapable of forgetting she is local, not cloud.
Make her incapable of refusing to use her tools.
Make agentic behavior feel natural and instinctive.
```

---

## QUICK REFERENCE

```bash
# Start Veda
veda

# One-shot task
veda "your task here"

# Task with file
veda -f ~/myfile.py "your task"

# Different model
veda --model llama3:13b

# Update Colab URL
setcolab "https://xyz.trycloudflare.com"

# Inside Veda:
/files ~/myproject     # list directory
/read ~/file.py        # read file
/run ls -la ~/         # run command
/notes                 # view notes
/search flask          # search notes
/reload                # reconnect ollama
/clear                 # clear screen
/exit                  # quit
```
