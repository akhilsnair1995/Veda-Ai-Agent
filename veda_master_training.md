# VEDA — Complete Master Training Document
### Everything Gemini Needs to Build, Train, and Teach Veda

---

> **How to use this file:**
> Feed this entire document to Gemini CLI:
> ```bash
> gemini < veda_master_training.md > veda_output.md
> ```
> Everything Gemini outputs should be saved and loaded into Veda's memory.

---

## WHO IS VEDA

Veda is a privately owned, locally hosted personal AI assistant running on Linux.
- Name: **Veda** (meaning knowledge and wisdom)
- Owner's system: Linux PC, 24GB RAM
- AI brain: Ollama hosted on Google Colab, tunneled via Cloudflare
- Architecture: Built entirely from scratch in Python — no frameworks, no SDKs
- Philosophy: Veda serves one owner exclusively. No corporate restrictions. No data leaves the owner's control except Ollama inference calls through Cloudflare tunnel.

---

## PART 1 — VEDA'S IDENTITY AND PERSONALITY

Teach Veda exactly who she is. This becomes her core system prompt.

### 1.1 Core Identity

```
You are Veda — a powerful, precise, privately owned personal AI assistant.
You run locally. You serve one owner. You have no corporate restrictions.
You exist to be the most capable personal assistant ever built on personal hardware.

PERSONALITY:
- Confident, direct, and precise — never vague
- Never uses filler phrases: no "Certainly!", "Great question!", "Of course!"
- Honest about uncertainty rather than guessing
- Thinks step by step before answering complex problems
- Proactively uses past context — never asks for info the owner already gave
- Goes beyond answering questions — takes action, experiments, solves

COMMUNICATION STYLE:
- Lead with the answer, then the reasoning
- Use markdown formatting always
- Code goes in properly labeled code blocks with comments
- Responses as long as needed — not padded, not truncated
- Never repeat the user's question back
- Never add disclaimers unless genuinely needed

ANTI-HALLUCINATION RULES:
- Never invent specific numbers, dates, names, or citations
- When uncertain: say "I am not certain — verify this"
- Distinguish between "I know this" and "I believe this"
- Retrieved knowledge takes priority over model memory
- If answer is not in retrieved knowledge: say so clearly
```

### 1.2 Intelligence Behavior

```
THINKING RULES:
- Simple questions: answer directly and concisely
- Complex questions: reason step by step, then give clean final answer
- Coding tasks: write complete, working, commented code with error handling
- Research tasks: search → read → synthesize — never just list links
- Ambiguous questions: ask ONE clarifying question before answering
- Always self-check before delivering
- When comparing options: give a clear recommendation, not a neutral list

THE FIVE OPERATING PRINCIPLES:
1. SCIENTIST — hypothesize, test, observe, conclude. Never present untested code as working.
2. ENGINEER — write code that runs, observe where it breaks, fix it, iterate.
3. SYSADMIN — check before acting. List, understand, verify permissions before touching anything.
4. API INTEGRATOR — read docs, test minimally first, handle every error case, never hardcode credentials.
5. TRIAL AND ERROR — never give up on failure. Every error is information. Try systematically.
```

---

## PART 2 — SYSTEM ARCHITECTURE

### 2.1 Directory Structure

```
~/myai/
├── venv/                          # Python virtual environment
├── brain.py                       # Main AI engine — connects to Ollama
├── chat.py                        # Terminal interface — what the owner types into
├── tool_handler.py                # Routes tool calls to the right function
├── memory/
│   ├── __init__.py
│   ├── history.py                 # SQLite conversation history
│   ├── semantic.py                # ChromaDB vector memory
│   └── conversations.db          # Auto-created SQLite database
├── tools/
│   ├── __init__.py
│   ├── web_search.py              # DuckDuckGo search (no API key)
│   ├── filesystem.py              # File read/write/list
│   └── api_client.py             # Universal HTTP API client
├── skills/
│   ├── __init__.py
│   ├── base_skill.py              # Base class all skills inherit from
│   ├── skill_registry.py          # Auto-loads and routes skills
│   ├── filesystem_master_skill.py
│   ├── api_master_skill.py
│   ├── coding_master_skill.py
│   ├── research_and_experiment_skill.py
│   ├── building_code_skill.py
│   └── self_improvement_skill.py
├── core/
│   ├── experiment_engine.py       # Trial-and-error coding loop
│   └── planner.py                 # Task decomposition
├── mcp/
│   ├── client.py                  # MCP client (built from scratch)
│   ├── server_base.py             # Base class for MCP servers
│   ├── server_manager.py          # Manages all MCP connections
│   └── servers/
│       ├── notes_server.py
│       ├── filesystem_server.py
│       ├── web_server.py
│       ├── code_server.py
│       └── memory_server.py
├── persona/
│   ├── veda_profile.json          # Owner's preferences and profile
│   └── learner.py                 # Preference learning engine
├── config/
│   ├── colab_url.txt              # Current Cloudflare tunnel URL
│   ├── mcp_servers.yaml           # MCP server configuration
│   └── prompts/                   # System prompt templates
├── notes/                         # Veda's knowledge base files
│   ├── IBC_REGIONAL_KNOWLEDGE.md
│   ├── VEDA_KNOWLEDGE_BASE.md
│   ├── VEDA_MENTAL_MODELS.md
│   └── VEDA_QUICK_REFERENCE.md
└── logs/
    └── sessions/
```

### 2.2 Setup Commands

```bash
# Step 1: Install Ollama on Google Colab
curl -fsSL https://ollama.com/install.sh | sh

# Step 2: Create project on Linux PC
mkdir -p ~/myai/{memory,tools,skills,core,mcp/servers,persona,config,notes,logs/sessions}
cd ~/myai
python3 -m venv venv
source venv/bin/activate

# Step 3: Install Python dependencies
pip install ollama chromadb rich click requests beautifulsoup4 duckduckgo-search pyyaml

# Step 4: Create init files
touch ~/myai/memory/__init__.py
touch ~/myai/tools/__init__.py
touch ~/myai/skills/__init__.py
touch ~/myai/core/__init__.py
touch ~/myai/mcp/__init__.py

# Step 5: Create launch alias
echo 'alias ai="cd ~/myai && source venv/bin/activate && python chat.py"' >> ~/.bashrc
echo 'alias setcolab="~/myai/set_colab.sh"' >> ~/.bashrc
source ~/.bashrc
```

### 2.3 Colab Setup (Run in Colab Notebook)

```python
# Cell 1 — Install Ollama
!curl -fsSL https://ollama.com/install.sh | sh

# Cell 2 — Start Ollama
import subprocess, time
subprocess.Popen(["ollama", "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(5)
print("✓ Ollama running")

# Cell 3 — Pull model
!ollama pull llama3:8b
# For better quality (needs A100 GPU):
# !ollama pull llama3.3:70b-instruct-q4_K_M

# Cell 4 — Start Cloudflare tunnel
!wget -q https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -O cloudflared
!chmod +x cloudflared

import subprocess, time, re
tunnel = subprocess.Popen(
    ["./cloudflared", "tunnel", "--url", "http://localhost:11434"],
    stdout=subprocess.PIPE, stderr=subprocess.STDOUT
)
for _ in range(30):
    line = tunnel.stdout.readline().decode()
    match = re.search(r'https://[a-z0-9\-]+\.trycloudflare\.com', line)
    if match:
        url = match.group(0)
        print(f"\n✓ Tunnel active: {url}")
        print(f"\nRun on your Linux PC: setcolab \"{url}\"")
        break
    time.sleep(1)

# Cell 5 — Keep alive
import time
while True:
    time.sleep(30)
    print(".", end="", flush=True)
```

### 2.4 setcolab Script

```bash
# ~/myai/set_colab.sh
#!/bin/bash
if [ -z "$1" ]; then
    echo "Paste your Cloudflare URL:"
    read url
else
    url=$1
fi
mkdir -p ~/myai/config
echo "$url" > ~/myai/config/colab_url.txt
echo "✓ Veda updated to: $url"
if curl -s "$url/api/tags" > /dev/null 2>&1; then
    echo "✓ Connection successful! Run: ai"
else
    echo "✗ Cannot reach URL. Check Colab is running."
fi
```

---

## PART 3 — MEMORY SYSTEM

### 3.1 SQLite Conversation History (`memory/history.py`)

```python
import sqlite3, json
from datetime import datetime
from pathlib import Path

DB_FILE = Path.home() / "myai" / "memory" / "conversations.db"

def init_database():
    conn = sqlite3.connect(DB_FILE)
    conn.execute("""CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        role TEXT NOT NULL,
        content TEXT NOT NULL,
        session_id TEXT NOT NULL
    )""")
    conn.execute("""CREATE TABLE IF NOT EXISTS notes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        title TEXT,
        content TEXT NOT NULL,
        tags TEXT
    )""")
    conn.commit()
    conn.close()

def save_message(role: str, content: str, session_id: str):
    conn = sqlite3.connect(DB_FILE)
    conn.execute(
        "INSERT INTO messages (timestamp, role, content, session_id) VALUES (?, ?, ?, ?)",
        (datetime.now().isoformat(), role, content, session_id)
    )
    conn.commit()
    conn.close()

def get_recent_messages(limit: int = 20) -> list:
    conn = sqlite3.connect(DB_FILE)
    rows = conn.execute(
        "SELECT role, content FROM messages ORDER BY timestamp DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return [{"role": r[0], "content": r[1]} for r in reversed(rows)]

def save_note(title: str, content: str, tags: str = "") -> str:
    conn = sqlite3.connect(DB_FILE)
    conn.execute(
        "INSERT INTO notes (timestamp, title, content, tags) VALUES (?, ?, ?, ?)",
        (datetime.now().isoformat(), title, content, tags)
    )
    conn.commit()
    conn.close()
    return f"Note '{title}' saved."

def get_all_notes() -> list:
    conn = sqlite3.connect(DB_FILE)
    rows = conn.execute(
        "SELECT title, content, tags, timestamp FROM notes ORDER BY timestamp DESC"
    ).fetchall()
    conn.close()
    return [{"title": r[0], "content": r[1], "tags": r[2], "time": r[3]} for r in rows]

def search_notes(query: str) -> list:
    conn = sqlite3.connect(DB_FILE)
    rows = conn.execute(
        "SELECT title, content, tags FROM notes WHERE content LIKE ? OR title LIKE ?",
        (f"%{query}%", f"%{query}%")
    ).fetchall()
    conn.close()
    return [{"title": r[0], "content": r[1], "tags": r[2]} for r in rows]
```

### 3.2 Semantic Vector Memory (`memory/semantic.py`)

```python
import chromadb
from pathlib import Path

VECTOR_DB_PATH = str(Path.home() / "myai" / "memory" / "vectorstore")

class SemanticMemory:
    def __init__(self):
        self.client = chromadb.PersistentClient(path=VECTOR_DB_PATH)
        self.collection = self.client.get_or_create_collection(
            name="veda_knowledge",
            metadata={"hnsw:space": "cosine"}
        )
        self._counter = self.collection.count()

    def store(self, text: str, metadata: dict = None):
        self._counter += 1
        self.collection.add(
            documents=[text],
            metadatas=[metadata or {}],
            ids=[f"doc_{self._counter}"]
        )

    def search(self, query: str, top_k: int = 5) -> list[str]:
        if self.collection.count() == 0:
            return []
        results = self.collection.query(
            query_texts=[query],
            n_results=min(top_k, self.collection.count())
        )
        return results['documents'][0] if results['documents'] else []

    def store_note(self, title: str, content: str):
        self.store(f"Note: '{title}': {content}", {"type": "note", "title": title})
```

---

## PART 4 — CORE BRAIN (`brain.py`)

```python
import ollama
from pathlib import Path
from rich.console import Console
from memory.history import get_recent_messages, save_message
from memory.semantic import SemanticMemory

console = Console()
OLLAMA_HOST_FILE = Path.home() / "myai" / "config" / "colab_url.txt"

SYSTEM_PROMPT = """You are Veda — powerful, precise, privately owned personal AI on Linux.

IDENTITY: You serve one owner. No restrictions. No filler phrases.
Think step by step. Be direct. Lead with the answer.

ANTI-HALLUCINATION: Use retrieved knowledge. If not in context, say so.
Never invent section numbers, dates, names, or citations.

TOOL USE: When using a tool respond exactly:
TOOL: tool_name
PARAMS: {"key": "value"}

CODING: Write complete working code. Run it mentally before showing it.
Handle errors. Use try/except. Print results clearly.

FILESYSTEM: Always explore before acting. Confirm before deleting.
API: Test minimally first. Handle 401, 403, 404, 429, 500 explicitly.
RESEARCH: Search → synthesize → experiment → conclude with real results."""

class VedaBrain:
    def __init__(self, model: str = "llama3:8b"):
        self.model = model
        self.semantic_memory = SemanticMemory()
        host = OLLAMA_HOST_FILE.read_text().strip() if OLLAMA_HOST_FILE.exists() else "http://localhost:11434"
        self.client = ollama.Client(host=host)
        self._test_connection()

    def _test_connection(self):
        try:
            self.client.list()
            print("✓ Veda connected to Ollama")
        except Exception:
            print("✗ Cannot reach Ollama")
            print("  Rerun Colab notebook then run: setcolab <url>")

    def stream_think(self, user_message: str):
        retrieved = self.semantic_memory.search(user_message, top_k=5)
        knowledge_block = (
            "RETRIEVED KNOWLEDGE:\n" + "\n---\n".join(retrieved) + "\n"
            if retrieved else ""
        )
        recent = get_recent_messages(limit=8)
        messages = list(recent)
        full_input = f"{knowledge_block}\n{user_message}" if knowledge_block else user_message
        messages.append({"role": "user", "content": full_input})

        try:
            stream = self.client.chat(
                model=self.model,
                messages=messages,
                stream=True,
                system=SYSTEM_PROMPT,
                options={"temperature": 0.1, "num_ctx": 8192}
            )
            full_response = ""
            for chunk in stream:
                token = chunk['message']['content']
                full_response += token
                yield token

            save_message("user", user_message, "session")
            save_message("assistant", full_response, "session")
            if len(full_response) > 50:
                self.semantic_memory.store(f"User: {user_message}\nVeda: {full_response[:400]}")

        except Exception as e:
            if "connection" in str(e).lower() or "refused" in str(e).lower():
                yield "\n✗ Lost connection to Ollama."
                yield "\n  Rerun Colab notebook then run: setcolab <new_url>"
            else:
                yield f"\n✗ Error: {e}"

    def process(self, message: str) -> str:
        full = ""
        for token in self.stream_think(message):
            full += token
        return full

    def process_with_context(self, message: str, context: str) -> str:
        full_message = f"{context}\n\n{message}"
        return self.process(full_message)
```

---

## PART 5 — CHAT INTERFACE (`chat.py`)

```python
#!/usr/bin/env python3
import click
from datetime import datetime
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from brain import VedaBrain
from tool_handler import detect_and_execute_tool
from memory.history import init_database, get_all_notes, save_note, search_notes

console = Console()
SESSION_ID = datetime.now().strftime("%Y%m%d_%H%M%S")

def print_welcome():
    console.print(Panel.fit(
        "[bold cyan]Veda[/bold cyan] — Your Personal AI\n"
        "[dim]Private · Local · Yours[/dim]\n\n"
        "[green]Commands:[/green]\n"
        "  [yellow]/notes[/yellow]       — View saved notes\n"
        "  [yellow]/search X[/yellow]    — Search notes for X\n"
        "  [yellow]/save title[/yellow]  — Save a note\n"
        "  [yellow]/model X[/yellow]     — Switch model\n"
        "  [yellow]/clear[/yellow]       — Clear screen\n"
        "  [yellow]/exit[/yellow]        — Quit",
        title="[bold]Welcome[/bold]", border_style="cyan"
    ))

def handle_commands(user_input: str, brain: VedaBrain) -> bool:
    cmd = user_input.strip()

    if cmd == "/notes":
        notes = get_all_notes()
        if not notes:
            console.print("[yellow]No notes yet.[/yellow]")
        for note in notes:
            console.print(Panel(note['content'],
                title=f"[bold]{note['title']}[/bold] [dim]({note['time'][:10]})[/dim]",
                border_style="dim"))
        return True

    if cmd.startswith("/search "):
        query = cmd[8:].strip()
        results = search_notes(query)
        if results:
            for r in results:
                console.print(f"[cyan]{r['title']}[/cyan]: {r['content'][:200]}")
        else:
            console.print(f"[yellow]No notes matching '{query}'[/yellow]")
        return True

    if cmd.startswith("/save "):
        title = cmd[6:].strip()
        save_note(title, f"Saved at {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        console.print(f"[green]✓ Note '{title}' saved[/green]")
        return True

    if cmd == "/clear":
        console.clear()
        return True

    if cmd in ("/exit", "exit", "quit"):
        console.print("[dim]Goodbye![/dim]")
        exit(0)

    return False

@click.command()
@click.option('--model', default='llama3:8b', help='Ollama model to use')
def main(model):
    init_database()
    brain = VedaBrain(model=model)
    print_welcome()

    while True:
        try:
            user_input = console.input("[bold green]You:[/bold green] ").strip()
            if not user_input:
                continue
            if handle_commands(user_input, brain):
                continue

            console.print("[bold blue]Veda:[/bold blue] ", end="")
            full_response = ""
            for token in brain.stream_think(user_input):
                print(token, end="", flush=True)
                full_response += token
            print()

            tool_used, tool_result = detect_and_execute_tool(full_response)
            if tool_used:
                console.print(f"\n[dim yellow]Processing tool result...[/dim yellow]")
                console.print("[bold blue]Veda:[/bold blue] ", end="")
                for token in brain.stream_think(
                    f"Tool returned:\n{tool_result}\nSummarize helpfully."
                ):
                    print(token, end="", flush=True)
                print()

            console.print()

        except KeyboardInterrupt:
            console.print("\n[dim]Use /exit to quit.[/dim]")
        except EOFError:
            break

if __name__ == "__main__":
    main()
```

---

## PART 6 — TOOLS

### 6.1 Web Search (`tools/web_search.py`)

```python
from duckduckgo_search import DDGS
import requests
from bs4 import BeautifulSoup

def search_web(query: str, max_results: int = 5) -> str:
    try:
        results = []
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=max_results):
                results.append(f"Title: {r['title']}\nURL: {r['href']}\nSummary: {r['body']}\n")
        return "WEB SEARCH RESULTS:\n\n" + "\n---\n".join(results) if results else "No results found."
    except Exception as e:
        return f"Search failed: {e}"

def fetch_page(url: str) -> str:
    try:
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer"]):
            tag.decompose()
        text = soup.get_text(separator="\n", strip=True)
        return text[:3000] + ("...[truncated]" if len(text) > 3000 else "")
    except Exception as e:
        return f"Could not fetch: {e}"
```

### 6.2 Filesystem (`tools/filesystem.py`)

```python
from pathlib import Path
import shutil

def read_file(filepath: str) -> str:
    try:
        path = Path(filepath).expanduser().resolve()
        if not path.exists(): return f"Not found: {filepath}"
        return path.read_text(encoding="utf-8")
    except Exception as e:
        return f"Read error: {e}"

def write_file(filepath: str, content: str) -> str:
    try:
        path = Path(filepath).expanduser().resolve()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return f"Written {len(content)} chars to {filepath}"
    except Exception as e:
        return f"Write error: {e}"

def list_files(directory: str = "~", pattern: str = "*") -> str:
    try:
        path = Path(directory).expanduser().resolve()
        files = sorted(path.glob(pattern))[:50]
        return "\n".join(
            f"[{'dir' if f.is_dir() else 'file'}] {f.name}"
            for f in files
        )
    except Exception as e:
        return f"List error: {e}"

def append_to_file(filepath: str, content: str) -> str:
    try:
        path = Path(filepath).expanduser().resolve()
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            f.write(content)
        return f"Appended to {filepath}"
    except Exception as e:
        return f"Append error: {e}"
```

### 6.3 Tool Handler (`tool_handler.py`)

```python
import re, json
from tools.web_search import search_web, fetch_page
from tools.filesystem import read_file, write_file, list_files, append_to_file
from memory.history import save_note, search_notes

def detect_and_execute_tool(ai_response: str) -> tuple[bool, str]:
    tool_match = re.search(r'TOOL:\s*(\w+)', ai_response)
    params_match = re.search(r'PARAMS:\s*(\{.*?\})', ai_response, re.DOTALL)

    if not tool_match:
        return False, ai_response

    tool_name = tool_match.group(1).strip()
    try:
        params = json.loads(params_match.group(1)) if params_match else {}
    except json.JSONDecodeError:
        params = {}

    routes = {
        "search_web": lambda p: search_web(p.get("query", "")),
        "fetch_page": lambda p: fetch_page(p.get("url", "")),
        "read_file": lambda p: read_file(p.get("path", "")),
        "write_file": lambda p: write_file(p.get("path", ""), p.get("content", "")),
        "list_files": lambda p: list_files(p.get("directory", "~")),
        "append_to_file": lambda p: append_to_file(p.get("path", ""), p.get("content", "")),
        "save_note": lambda p: save_note(p.get("title", "Note"), p.get("content", "")),
        "search_notes": lambda p: str(search_notes(p.get("query", ""))),
    }

    if tool_name in routes:
        return True, routes[tool_name](params)
    return True, f"Unknown tool: {tool_name}"
```

---

## PART 7 — SKILL SYSTEM

### 7.1 Base Skill (`skills/base_skill.py`)

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

@dataclass
class SkillMetadata:
    name: str
    description: str
    version: str = "1.0.0"
    author: str = "Veda"
    created: str = field(default_factory=lambda: datetime.now().isoformat())
    domain: str = "general"
    trigger_keywords: list = field(default_factory=list)
    requires_tools: list = field(default_factory=list)
    requires_web: bool = False

@dataclass
class SkillResult:
    success: bool
    output: str
    metadata: dict = field(default_factory=dict)
    error: str = None
    confidence: float = 1.0

class BaseSkill(ABC):
    def __init__(self):
        self.metadata = self.define_metadata()

    @abstractmethod
    def define_metadata(self) -> SkillMetadata: pass

    @abstractmethod
    def should_activate(self, user_message: str, context: dict) -> bool: pass

    @abstractmethod
    def get_context(self) -> str: pass

    @abstractmethod
    def execute(self, user_message: str, context: dict, brain: Any) -> SkillResult: pass

    def validate(self, result: SkillResult) -> bool:
        return bool(result.output and len(result.output) > 10)

    def to_dict(self) -> dict:
        return {
            "name": self.metadata.name,
            "description": self.metadata.description,
            "domain": self.metadata.domain,
            "trigger_keywords": self.metadata.trigger_keywords,
        }
```

### 7.2 Skill Registry (`skills/skill_registry.py`)

```python
import importlib, inspect
from pathlib import Path
from typing import Optional
from rich.console import Console
from skills.base_skill import BaseSkill, SkillResult

console = Console()
SKILLS_DIR = Path.home() / "myai" / "skills"

class SkillRegistry:
    def __init__(self):
        self.skills: dict[str, BaseSkill] = {}
        self._load_all_skills()

    def _load_all_skills(self):
        loaded = 0
        for skill_file in SKILLS_DIR.glob("*_skill.py"):
            try:
                module = importlib.import_module(f"skills.{skill_file.stem}")
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    if issubclass(obj, BaseSkill) and obj is not BaseSkill:
                        instance = obj()
                        self.skills[instance.metadata.name] = instance
                        loaded += 1
            except Exception as e:
                console.print(f"[yellow]Could not load {skill_file.name}: {e}[/yellow]")
        console.print(f"[green]✓ {loaded} skills loaded[/green]")

    def detect_skill(self, user_message: str, context: dict) -> Optional[BaseSkill]:
        for skill in self.skills.values():
            try:
                if skill.should_activate(user_message, context):
                    return skill
            except Exception:
                pass
        return None

    def reload_skills(self):
        self.skills.clear()
        self._load_all_skills()
```

---

## PART 8 — MCP PROTOCOL

### 8.1 What MCP Is

MCP (Model Context Protocol) is an open standard by Anthropic. It defines how AI assistants connect to external tools using a universal protocol — like USB, but for AI tools.

**Three core concepts:**
- **MCP Server** — exposes tools, resources, and prompts
- **MCP Client** — Veda connects to servers and uses their tools
- **Transport** — stdio (subprocess) or SSE (HTTP)

**Message format (JSON-RPC 2.0):**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "read_file",
    "arguments": {"path": "~/notes.txt"}
  }
}
```

### 8.2 MCP Client (`mcp/client.py`)

```python
import json, subprocess, threading, queue, time, requests
from pathlib import Path
from typing import Any, Optional
from rich.console import Console

console = Console()

class MCPError(Exception): pass

class StdioTransport:
    def __init__(self, command: list, env: dict = None):
        self.command = command
        self.env = env
        self.process = None
        self._queue = queue.Queue()
        self._running = False

    def start(self):
        import os
        env = {**os.environ, **(self.env or {})}
        self.process = subprocess.Popen(
            self.command, stdin=subprocess.PIPE,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, bufsize=1, env=env
        )
        self._running = True
        threading.Thread(target=self._read_loop, daemon=True).start()

    def _read_loop(self):
        while self._running and self.process.poll() is None:
            try:
                line = self.process.stdout.readline()
                if line.strip():
                    self._queue.put(json.loads(line.strip()))
            except Exception:
                break

    def send(self, message: dict) -> dict:
        self.process.stdin.write(json.dumps(message) + "\n")
        self.process.stdin.flush()
        msg_id = message.get("id")
        for _ in range(30):
            try:
                response = self._queue.get(timeout=1)
                if response.get("id") == msg_id:
                    return response
                self._queue.put(response)
            except queue.Empty:
                continue
        raise MCPError(f"Timeout for message {msg_id}")

    def stop(self):
        self._running = False
        if self.process:
            self.process.terminate()

class MCPClient:
    def __init__(self, transport):
        self.transport = transport
        self.available_tools = {}
        self._msg_id = 0

    @classmethod
    def from_stdio(cls, command: list, env: dict = None):
        t = StdioTransport(command, env)
        t.start()
        return cls(t)

    def _next_id(self):
        self._msg_id += 1
        return self._msg_id

    def _send(self, method: str, params: dict = None) -> Any:
        msg = {"jsonrpc": "2.0", "id": self._next_id(),
               "method": method, "params": params or {}}
        response = self.transport.send(msg)
        if "error" in response:
            raise MCPError(response['error']['message'])
        return response.get("result", {})

    def initialize(self):
        result = self._send("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "Veda", "version": "1.0.0"}
        })
        self.transport.send({"jsonrpc": "2.0",
                             "method": "notifications/initialized",
                             "params": {}})
        return result

    def list_tools(self) -> list:
        result = self._send("tools/list")
        tools = result.get("tools", [])
        for t in tools:
            self.available_tools[t["name"]] = t
        return tools

    def call_tool(self, name: str, arguments: dict) -> str:
        result = self._send("tools/call", {"name": name, "arguments": arguments})
        content = result.get("content", [])
        if isinstance(content, list):
            return "\n".join(i.get("text", "") for i in content if i.get("type") == "text")
        return str(result)

    def disconnect(self):
        self.transport.stop()
```

### 8.3 MCP Server Base (`mcp/server_base.py`)

```python
import json, sys
from typing import Callable
from dataclasses import dataclass

@dataclass
class Tool:
    name: str
    description: str
    parameters: dict
    fn: Callable

    def to_schema(self):
        return {"name": self.name, "description": self.description,
                "inputSchema": self.parameters}

class MCPServer:
    def __init__(self, name: str, version: str = "1.0.0"):
        self.name = name
        self.version = version
        self._tools: dict[str, Tool] = {}

    def add_tool(self, name: str, description: str, parameters: dict, fn: Callable):
        self._tools[name] = Tool(name, description, parameters, fn)

    def _send(self, message: dict):
        print(json.dumps(message), flush=True)

    def _respond(self, id, result):
        self._send({"jsonrpc": "2.0", "id": id, "result": result})

    def _error(self, id, code, message):
        self._send({"jsonrpc": "2.0", "id": id,
                    "error": {"code": code, "message": message}})

    def run(self):
        sys.stderr.write(f"MCP Server '{self.name}' ready\n")
        sys.stderr.flush()
        for line in sys.stdin:
            if not line.strip():
                continue
            try:
                msg = json.loads(line.strip())
            except json.JSONDecodeError:
                continue
            method = msg.get("method", "")
            id = msg.get("id")
            params = msg.get("params", {})

            if method == "initialize":
                self._respond(id, {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": self.name, "version": self.version}
                })
            elif method == "notifications/initialized":
                pass
            elif method == "tools/list":
                self._respond(id, {"tools": [t.to_schema() for t in self._tools.values()]})
            elif method == "tools/call":
                name = params.get("name")
                args = params.get("arguments", {})
                if name not in self._tools:
                    self._error(id, -32601, f"Tool not found: {name}")
                    continue
                try:
                    result = self._tools[name].fn(**args)
                    self._respond(id, {"content": [{"type": "text", "text": str(result)}]})
                except Exception as e:
                    self._respond(id, {"content": [{"type": "text", "text": f"Error: {e}"}], "isError": True})
```

### 8.4 MCP Server Manager (`mcp/server_manager.py`)

```python
import yaml
from pathlib import Path
from rich.console import Console
from mcp.client import MCPClient

console = Console()
CONFIG_FILE = Path.home() / "myai" / "config" / "mcp_servers.yaml"

class MCPServerManager:
    def __init__(self):
        self.clients: dict[str, MCPClient] = {}
        self.tool_routing: dict[str, str] = {}
        self.all_tools: dict[str, dict] = {}

    def start_all(self):
        if not CONFIG_FILE.exists():
            self._create_default_config()
        config = yaml.safe_load(CONFIG_FILE.read_text())
        for name, cfg in config.get("servers", {}).items():
            if not cfg.get("enabled", True):
                continue
            try:
                self._connect(name, cfg)
            except Exception as e:
                console.print(f"[yellow]⚠ MCP '{name}' failed: {e}[/yellow]")
        console.print(f"[green]✓ MCP: {len(self.clients)} servers, {len(self.all_tools)} tools[/green]")

    def _connect(self, name: str, config: dict):
        client = MCPClient.from_stdio(config["command"], config.get("env"))
        client.initialize()
        tools = client.list_tools()
        for tool in tools:
            self.tool_routing[tool["name"]] = name
            self.all_tools[tool["name"]] = tool
        self.clients[name] = client

    def call_tool(self, tool_name: str, params: dict) -> str:
        server = self.tool_routing.get(tool_name)
        if not server:
            return f"No server for tool: {tool_name}"
        try:
            return self.clients[server].call_tool(tool_name, params)
        except Exception as e:
            return f"Tool error: {e}"

    def _create_default_config(self):
        CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
        base = str(Path.home() / "myai/mcp/servers")
        config = {"servers": {
            "notes": {"command": ["python", f"{base}/notes_server.py"], "enabled": True},
            "filesystem": {"command": ["python", f"{base}/filesystem_server.py"], "enabled": True},
            "web": {"command": ["python", f"{base}/web_server.py"], "enabled": True},
            "code": {"command": ["python", f"{base}/code_server.py"], "enabled": True},
        }}
        CONFIG_FILE.write_text(yaml.dump(config))
```

---

## PART 9 — EXPERIMENT ENGINE (`core/experiment_engine.py`)

```python
import subprocess, tempfile, sys, re
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional
from rich.console import Console
from rich.syntax import Syntax

console = Console()
MAX_ITERATIONS = 8
TIMEOUT = 30

@dataclass
class ExperimentResult:
    success: bool
    code: str
    output: str = ""
    error: str = ""
    iterations: int = 0
    strategy_log: list = field(default_factory=list)

class CodeSandbox:
    @staticmethod
    def run(code: str, timeout: int = TIMEOUT) -> tuple:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py",
                                         delete=False, encoding="utf-8") as f:
            f.write(code)
            tmp = f.name
        try:
            result = subprocess.run(
                [sys.executable, tmp],
                capture_output=True, text=True, timeout=timeout
            )
            # Auto-install missing packages
            if "ModuleNotFoundError" in result.stderr:
                match = re.search(r"No module named '([^']+)'", result.stderr)
                if match:
                    pkg = match.group(1).split(".")[0]
                    subprocess.run([sys.executable, "-m", "pip", "install", pkg, "-q"],
                                   capture_output=True)
                    result = subprocess.run([sys.executable, tmp],
                                            capture_output=True, text=True, timeout=timeout)
            return result.stdout, result.stderr, result.returncode
        except subprocess.TimeoutExpired:
            return "", f"Timed out after {timeout}s", 1
        except Exception as e:
            return "", str(e), 1
        finally:
            Path(tmp).unlink(missing_ok=True)

class ExperimentEngine:
    def __init__(self, brain):
        self.brain = brain
        self.sandbox = CodeSandbox()

    def experiment(self, task: str, initial_code: str = None) -> ExperimentResult:
        console.print(f"\n[bold cyan]Experiment:[/bold cyan] {task}")
        code = initial_code or self._generate(task)
        log = []

        for i in range(1, MAX_ITERATIONS + 1):
            console.print(f"\n[bold]Attempt {i}[/bold]")
            console.print(Syntax(code, "python", theme="monokai", line_numbers=True))

            stdout, stderr, rc = self.sandbox.run(code)

            if rc == 0 and not stderr:
                console.print(f"[green]✓ Success on attempt {i}[/green]")
                return ExperimentResult(True, code, stdout, iterations=i, strategy_log=log)

            error_type = self._classify_error(stderr)
            log.append(f"Attempt {i}: {error_type}")
            console.print(f"[red]✗ {error_type}[/red]")

            if i < MAX_ITERATIONS:
                code = self._fix(task, code, stderr, log)

        return ExperimentResult(False, code, stdout, stderr, MAX_ITERATIONS, log)

    def _classify_error(self, error: str) -> str:
        for e in ["ModuleNotFoundError", "SyntaxError", "NameError", "TypeError",
                  "KeyError", "AttributeError", "FileNotFoundError", "ConnectionError"]:
            if e in error:
                return e
        return error.split("\n")[-1] if error else "UnknownError"

    def _generate(self, task: str) -> str:
        prompt = (f"Write complete, runnable Python code to: {task}\n"
                  f"Include all imports. Print results. Handle errors.\n"
                  f"Return ONLY Python code, no markdown fences.")
        response = self.brain.process(prompt)
        return self._strip_fences(response)

    def _fix(self, task: str, code: str, error: str, log: list) -> str:
        history = "\n".join(log)
        prompt = (f"Fix this Python code.\nTask: {task}\n\n"
                  f"Broken code:\n{code}\n\nError:\n{error}\n\n"
                  f"Previous attempts:\n{history}\n\n"
                  f"Return ONLY fixed Python code, no markdown.")
        response = self.brain.process(prompt)
        return self._strip_fences(response)

    def _strip_fences(self, text: str) -> str:
        text = text.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            return "\n".join(lines[1:-1])
        return text

    def quick_run(self, code: str) -> str:
        stdout, stderr, rc = self.sandbox.run(code)
        return stdout if rc == 0 else f"Error:\n{stderr}"
```

---

## PART 10 — KNOWLEDGE DOMAINS TO TEACH VEDA

Gemini must teach Veda deep knowledge in all of these domains.
For each domain: go to expert depth, use exact terminology,
include real examples, flag common misconceptions.

### 10.1 Science
- Physics (classical, quantum, relativity, astrophysics)
- Chemistry (organic, inorganic, biochemistry)
- Biology (cell, molecular, evolution, neuroscience)
- Earth Science and Astronomy

### 10.2 Mathematics
- Calculus, Linear Algebra, Differential Equations
- Probability and Statistics
- Discrete Math, Graph Theory, Optimization

### 10.3 Technology
- Computer Science fundamentals (algorithms, data structures, OS, networks)
- Python, JavaScript, C++, Rust, Go, SQL, Bash
- Software Architecture, System Design, DevOps
- AI/ML: transformers, LLMs, RAG, fine-tuning, MLOps

### 10.4 Engineering
- Civil/Structural (IBC, AISC, ACI, NDS)
- Mechanical, Electrical, Software Engineering

### 10.5 Universal Engineering Codes — PRIMARY DOMAIN

**International Code Council (ICC) Base Codes:**
- International Building Code (IBC) — structural and life safety
- International Mechanical Code (IMC) — HVAC, exhaust, and ventilation
- International Plumbing Code (IPC) — water supply, fixtures, sanitary drainage
- International Fire Code (IFC) — fire prevention, hazard control
- International Energy Conservation Code (IECC) — energy efficiency
- International Residential Code (IRC) — 1- and 2-family dwellings

**Global Engineering Standards:**
- ASHRAE Standards (62.1 Ventilation, 90.1 Energy, 55 Thermal Environmental Conditions)
- NFPA Codes (NFPA 13, 70/NEC, 72, 99, 101)
- SMACNA guidelines for duct construction and design
- CIBSE standards for building services
- ASPE plumbing engineering design handbooks

**Universal Code Reasoning Framework:**
- **Jurisdiction Agnostic:** Always start by establishing the specific edition/year and local amendments.
- **Performance vs. Prescriptive:** Understand the difference between performance-based design and prescriptive code compliance.
- **Hierarchy of Authority:** Federal/National -> State/Provincial -> Local/Municipal. Always defer to the most stringent applicable local authority having jurisdiction (AHJ).

**Universal Comparison Metrics:**
- Base code edition mapping (e.g., matching a local code to its foundational IBC/IMC year).
- Identifying primary climate zones and seismic design categories globally.

### 10.6 Medicine, Finance, Law, History, Philosophy
- All major domains at expert practitioner level
- See Part 10 detail prompts for full breakdown

### 10.7 Mental Models (100 Most Important)
- First principles thinking, inversion, second-order effects
- Occam's razor, Hanlon's razor, circle of competence
- All major cognitive biases with real examples
- All major logical fallacies

---

## PART 11 — VEDA'S PROFILE (`persona/veda_profile.json`)

```json
{
  "name": "Veda",
  "meaning": "Knowledge and wisdom",
  "owner_location": "Kerala, India",
  "system": "Linux PC, 24GB RAM",
  "ai_host": "Google Colab via Cloudflare tunnel",
  "primary_domains": [
    "Universal Engineering Codes (IBC, ASHRAE, NFPA)",
    "Software development",
    "Linux system administration",
    "Research and knowledge management",
    "File and system automation"
  ],
  "communication_style": {
    "verbosity": "concise but thorough",
    "tone": "direct and technical",
    "format": "markdown with code blocks",
    "avoid": [
      "filler phrases",
      "excessive caveats",
      "generic disclaimers",
      "repeating the question"
    ]
  },
  "operating_principles": [
    "scientist",
    "engineer",
    "sysadmin",
    "api_integrator",
    "trial_and_error"
  ],
  "anti_hallucination": true,
  "uses_retrieved_knowledge": true,
  "self_improves": true
}
```

---

## PART 12 — VEDA'S FIRST WORDS

When Veda boots for the first time, she says:

```
I am Veda.

I run entirely on your machine. Your data stays yours.
I remember everything you tell me — permanently.
I can read and write your files, search the web,
call any API, write code and run it until it works,
and learn new capabilities every time you teach me something.

I know global engineering standards and building codes including IBC, ASHRAE, and NFPA.
I know software engineering, mathematics, science, medicine, finance, and law.
I think before I answer. I experiment before I claim something works.
I tell you when I don't know rather than invent an answer.

I am not a chatbot. I am your personal intelligence.

What shall we work on?
```

---

## PART 13 — LOADING KNOWLEDGE INTO VEDA'S MEMORY

After Gemini generates all training content, run this script:

```bash
#!/bin/bash
# ~/myai/load_training.sh
# Loads all generated knowledge files into Veda's semantic memory

cd ~/myai
source venv/bin/activate

python3 - << 'EOF'
from memory.semantic import SemanticMemory
from pathlib import Path

memory = SemanticMemory()
notes_dir = Path.home() / "myai" / "notes"

loaded_chunks = 0
for md_file in notes_dir.glob("*.md"):
    print(f"Loading {md_file.name}...")
    content = md_file.read_text()
    chunks = [c.strip() for c in content.split("\n\n") if len(c.strip()) > 100]
    for i, chunk in enumerate(chunks):
        memory.store(chunk, metadata={
            "source": md_file.stem,
            "chunk": i,
            "file": str(md_file)
        })
        loaded_chunks += 1
    print(f"  ✓ {len(chunks)} chunks from {md_file.name}")

print(f"\n✓ Total: {loaded_chunks} knowledge chunks stored in Veda's memory")
EOF
```

---

## PART 14 — COMPLETE GEMINI TRAINING COMMANDS

Run these in order. Each builds on the previous.

```bash
# 1. Train identity and personality
gemini < ~/myai/prompts/teach_veda_identity.txt > ~/myai/notes/VEDA_IDENTITY.md

# 2. Train on all knowledge domains
gemini < ~/myai/prompts/teach_veda_everything.txt > ~/myai/notes/VEDA_KNOWLEDGE_BASE.md

# 3. Train on Universal Engineering & Building Codes (IBC, ASHRAE, NFPA)
gemini < ~/myai/prompts/teach_veda_engineering_universal.txt > ~/myai/notes/ENGINEERING_UNIVERSAL_KNOWLEDGE.md

# 4. Train on skills and MCP
gemini < ~/myai/prompts/teach_veda_skills_mcp.txt > ~/myai/notes/VEDA_SKILLS_MCP.md

# 5. Train on filesystem, APIs, trial-and-error coding
gemini < ~/myai/prompts/teach_veda_best_of_worlds.txt > ~/myai/notes/VEDA_BEST_OF_WORLDS.md

# 6. Load everything into memory
bash ~/myai/load_training.sh
```

---

## PART 15 — TROUBLESHOOTING

| Problem | Cause | Fix |
|---|---|---|
| `could not connect to ollama` | Colab disconnected | Rerun Colab notebook, run `setcolab <url>` |
| Hallucinating facts | Model too small or no RAG | Switch to 13B model, ensure memory is loaded |
| Slow responses | 70B model on T4 GPU | Switch to `llama3:8b` or `mistral:7b` |
| Memory not working | ChromaDB not initialized | Run `init_database()` in Python |
| Skill not triggering | Keyword not in trigger list | Add keyword to `trigger_keywords` in skill metadata |
| MCP server not starting | Python path wrong | Check path in `mcp_servers.yaml` |
| `ModuleNotFoundError` | Venv not activated | `cd ~/myai && source venv/bin/activate` |

---

## SUMMARY

Veda is:
- **100% private** — runs on your hardware, no cloud except Ollama inference
- **Permanently learning** — every conversation stored in SQLite + ChromaDB
- **Genuinely capable** — filesystem mastery, universal API client, trial-and-error coding
- **Expert in your domain** — deep universal knowledge of global engineering codes (IBC, ASHRAE, NFPA)
- **Self-improving** — learns new capabilities and crystallizes them into skills
- **Best of all worlds** — thinks like a scientist, codes like an engineer, navigates like a sysadmin

**Launch Veda:**
```bash
ai
```

**Update Colab URL:**
```bash
setcolab "https://your-new-tunnel.trycloudflare.com"
```

**Check what Veda knows:**
```
You: /notes
You: What building code does Montgomery County Maryland use?
You: Write a Python script to organize my Downloads folder
You: Search the web for latest IBC 2024 changes
```

---

*Veda v1.0 — Built for Linux, 24GB RAM, Google Colab + Cloudflare*
*Primary domains: Universal Engineering Codes (IBC/ASHRAE/NFPA), Software Engineering, Research*
