# mcp/servers/notes_server.py
import sys
from pathlib import Path

# Setup path so we can import from veda_agent packages like memory.history if needed, 
# or just use sqlite directly here. We will use sqlite directly to ensure it acts as an independent MCP server.
import sqlite3
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR))
from mcp.server_base import MCPServer

DB_PATH = BASE_DIR / "memory" / "history.db"

def _init_db():
    if not DB_PATH.parent.exists():
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Assuming standard table from memory.history, or we create our own notes table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT UNIQUE,
            content TEXT,
            tags TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

_init_db()

server = MCPServer(name="notes", version="1.0.0")

def create_note(title: str, content: str, tags: str = "") -> str:
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO notes (title, content, tags) VALUES (?, ?, ?)", (title, content, tags))
        conn.commit()
        conn.close()
        return f"Note '{title}' created successfully."
    except sqlite3.IntegrityError:
        return f"Note '{title}' already exists."

def read_note(title: str) -> str:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT content FROM notes WHERE title = ?", (title,))
    result = cursor.fetchone()
    conn.close()
    if result:
        return result[0]
    return f"Note '{title}' not found."

def update_note(title: str, content: str) -> str:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE notes SET content = ?, updated_at = CURRENT_TIMESTAMP WHERE title = ?", (content, title))
    if cursor.rowcount > 0:
        conn.commit()
        conn.close()
        return f"Note '{title}' updated."
    conn.close()
    return f"Note '{title}' not found."

def delete_note(title: str) -> str:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM notes WHERE title = ?", (title,))
    if cursor.rowcount > 0:
        conn.commit()
        conn.close()
        return f"Note '{title}' deleted."
    conn.close()
    return f"Note '{title}' not found."

def search_notes(query: str) -> str:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT title, content FROM notes WHERE title LIKE ? OR content LIKE ?", (f"%{query}%", f"%{query}%"))
    results = cursor.fetchall()
    conn.close()
    if not results:
        return f"No notes found matching '{query}'."
    
    output = []
    for title, content in results:
        output.append(f"Title: {title}
Preview: {content[:100]}...
---")
    return "
".join(output)

def list_notes(tag: str = None) -> str:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    if tag:
        cursor.execute("SELECT title, tags FROM notes WHERE tags LIKE ?", (f"%{tag}%",))
    else:
        cursor.execute("SELECT title, tags FROM notes")
    results = cursor.fetchall()
    conn.close()
    if not results:
        return "No notes found."
    return "
".join([f"- {t} (Tags: {tg})" for t, tg in results])

def append_to_note(title: str, content: str) -> str:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT content FROM notes WHERE title = ?", (title,))
    result = cursor.fetchone()
    if result:
        new_content = result[0] + "
" + content
        cursor.execute("UPDATE notes SET content = ?, updated_at = CURRENT_TIMESTAMP WHERE title = ?", (new_content, title))
        conn.commit()
        conn.close()
        return f"Appended to '{title}'."
    conn.close()
    return f"Note '{title}' not found."

# Resources
def get_all_notes():
    return list_notes()

def get_recent_notes():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT title FROM notes ORDER BY updated_at DESC LIMIT 10")
    results = cursor.fetchall()
    conn.close()
    return "
".join([f"- {r[0]}" for r in results])

# Register tools
server.add_tool("create_note", "Create a new note", 
    {"type": "object", "properties": {"title": {"type": "string"}, "content": {"type": "string"}, "tags": {"type": "string"}}, "required": ["title", "content"]}, 
    create_note)
server.add_tool("read_note", "Read a note by title", 
    {"type": "object", "properties": {"title": {"type": "string"}}, "required": ["title"]}, 
    read_note)
server.add_tool("update_note", "Update an existing note", 
    {"type": "object", "properties": {"title": {"type": "string"}, "content": {"type": "string"}}, "required": ["title", "content"]}, 
    update_note)
server.add_tool("delete_note", "Delete a note", 
    {"type": "object", "properties": {"title": {"type": "string"}}, "required": ["title"]}, 
    delete_note)
server.add_tool("search_notes", "Search across all notes", 
    {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}, 
    search_notes)
server.add_tool("list_notes", "List all notes, optionally filtered by tag", 
    {"type": "object", "properties": {"tag": {"type": "string"}}}, 
    list_notes)
server.add_tool("append_to_note", "Append content to an existing note", 
    {"type": "object", "properties": {"title": {"type": "string"}, "content": {"type": "string"}}, "required": ["title", "content"]}, 
    append_to_note)

# Register resources
server.add_resource("notes://all", "All Notes", "Stream of all notes", get_all_notes)
server.add_resource("notes://recent", "Recent Notes", "Last 10 notes", get_recent_notes)

if __name__ == "__main__":
    server.run()
