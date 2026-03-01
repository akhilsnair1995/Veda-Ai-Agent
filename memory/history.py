# memory/history.py
# This file manages your conversation history database.
# Think of it as a chat log that never gets deleted.

import sqlite3
import json
from datetime import datetime
from pathlib import Path

# Use a relative path so it works on both Windows and WSL
BASE_DIR = Path(__file__).resolve().parent.parent
DB_FILE = BASE_DIR / "memory" / "conversations.db"

def init_database():
    """
    Create the database tables if they don't exist yet.
    This runs every time the chatbot starts but only creates
    tables on the very first run.
    """
    conn = sqlite3.connect(DB_FILE)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            role TEXT NOT NULL,        -- 'user' or 'assistant'
            content TEXT NOT NULL,     -- the actual message
            session_id TEXT NOT NULL   -- groups messages by conversation session
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            title TEXT,
            content TEXT NOT NULL,
            tags TEXT                  -- comma-separated tags
        )
    """)
    conn.commit()
    conn.close()


def save_message(role: str, content: str, session_id: str):
    """
    Save a single message to the database.
    role is either 'user' (you) or 'assistant' (the AI).
    """
    conn = sqlite3.connect(DB_FILE)
    conn.execute(
        "INSERT INTO messages (timestamp, role, content, session_id) VALUES (?, ?, ?, ?)",
        (datetime.now().isoformat(), role, content, session_id)
    )
    conn.commit()
    conn.close()


def get_recent_messages(limit: int = 20) -> list:
    """
    Get the last N messages from the database.
    These are injected into the AI's context so it remembers
    what you were just talking about.
    """
    conn = sqlite3.connect(DB_FILE)
    rows = conn.execute(
        "SELECT role, content FROM messages ORDER BY timestamp DESC LIMIT ?",
        (limit,)
    ).fetchall()
    conn.close()
    # Reverse so oldest message comes first (correct order for AI context)
    return [{"role": row[0], "content": row[1]} for row in reversed(rows)]


def save_note(title: str, content: str, tags: str = ""):
    """
    Save a personal note to the database.
    You can ask the AI to save notes for you, or save them directly.
    """
    conn = sqlite3.connect(DB_FILE)
    conn.execute(
        "INSERT INTO notes (timestamp, title, content, tags) VALUES (?, ?, ?, ?)",
        (datetime.now().isoformat(), title, content, tags)
    )
    conn.commit()
    conn.close()
    return f"Note '{title}' saved successfully."


def get_all_notes() -> list:
    """Retrieve all saved notes."""
    conn = sqlite3.connect(DB_FILE)
    rows = conn.execute(
        "SELECT title, content, tags, timestamp FROM notes ORDER BY timestamp DESC"
    ).fetchall()
    conn.close()
    return [{"title": r[0], "content": r[1], "tags": r[2], "time": r[3]} for r in rows]


def search_notes(query: str) -> list:
    """Search notes by keyword."""
    conn = sqlite3.connect(DB_FILE)
    rows = conn.execute(
        "SELECT title, content, tags FROM notes WHERE content LIKE ? OR title LIKE ?",
        (f"%{query}%", f"%{query}%")
    ).fetchall()
    conn.close()
    return [{"title": r[0], "content": r[1], "tags": r[2]} for r in rows]
