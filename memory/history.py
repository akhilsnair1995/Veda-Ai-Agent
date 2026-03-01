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
    """Create tables if they don't exist."""
    conn = sqlite3.connect(DB_FILE)
    
    # Session Management Table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            session_id TEXT PRIMARY KEY,
            title TEXT,
            workspace_path TEXT,
            is_pinned INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Messages Table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            session_id TEXT NOT NULL,
            FOREIGN KEY(session_id) REFERENCES sessions(session_id)
        )
    """)
    
    # Notes Table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            title TEXT,
            content TEXT NOT NULL,
            tags TEXT DEFAULT ''
        )
    """)
    conn.commit()
    conn.close()

def create_session(session_id: str, title: str, workspace_path: str):
    conn = sqlite3.connect(DB_FILE)
    conn.execute(
        "INSERT OR IGNORE INTO sessions (session_id, title, workspace_path) VALUES (?, ?, ?)",
        (session_id, title, workspace_path)
    )
    conn.commit()
    conn.close()

def get_all_sessions():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT * FROM sessions ORDER BY is_pinned DESC, created_at DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]

def delete_session(session_id: str):
    conn = sqlite3.connect(DB_FILE)
    conn.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
    conn.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
    conn.commit()
    conn.close()

def toggle_pin_session(session_id: str):
    conn = sqlite3.connect(DB_FILE)
    conn.execute("UPDATE sessions SET is_pinned = 1 - is_pinned WHERE session_id = ?", (session_id,))
    conn.commit()
    conn.close()

def get_session_messages(session_id: str) -> list:
    conn = sqlite3.connect(DB_FILE)
    rows = conn.execute(
        "SELECT role, content FROM messages WHERE session_id = ? ORDER BY timestamp ASC",
        (session_id,)
    ).fetchall()
    conn.close()
    return [{"role": r[0], "content": r[1]} for r in rows]

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
        "SELECT role, content FROM messages ORDER BY timestamp DESC LIMIT ?",
        (limit,)
    ).fetchall()
    conn.close()
    return [{"role": row[0], "content": row[1]} for row in reversed(rows)]

def save_note(title: str, content: str, tags: str = ""):
    conn = sqlite3.connect(DB_FILE)
    conn.execute(
        "INSERT INTO notes (timestamp, title, content, tags) VALUES (?, ?, ?, ?)",
        (datetime.now().isoformat(), title, content, tags)
    )
    conn.commit()
    conn.close()
    return f"Note '{title}' saved successfully."

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
