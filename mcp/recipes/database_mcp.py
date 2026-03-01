# mcp/recipes/database_mcp.py
# RECIPE 1 — DATABASE MCP SERVER
# Wraps a SQLite database as an MCP Server.
# This pattern applies to PostgreSQL, MySQL, etc.

import sqlite3
import json
from pathlib import Path
from mcp.server_base import MCPServer

server = MCPServer(name="database", version="1.0.0")
DB_PATH = "example.db" # Customize this path

def _connect():
    return sqlite3.connect(DB_PATH)

def run_query(query: str, params: list = None) -> str:
    """Safely execute a SQL query."""
    # Prevent destructive queries if needed
    if not query.strip().upper().startswith("SELECT"):
        return "Error: Read-only server. Only SELECT allowed."
        
    try:
        conn = _connect()
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        if params:
            c.execute(query, params)
        else:
            c.execute(query)
            
        rows = c.fetchall()
        conn.close()
        
        result = [dict(row) for row in rows]
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Database error: {e}"

def inspect_schema() -> str:
    """Return the schema of all tables."""
    try:
        conn = _connect()
        c = conn.cursor()
        c.execute("SELECT name, sql FROM sqlite_master WHERE type='table'")
        tables = c.fetchall()
        conn.close()
        
        schema = []
        for name, sql in tables:
            schema.append(f"-- Table: {name}
{sql}
")
        return "
".join(schema)
    except Exception as e:
        return f"Schema extraction error: {e}"

server.add_tool("run_query", "Execute a SELECT query safely",
    {"type": "object", "properties": {"query": {"type": "string"}, "params": {"type": "array"}}, "required": ["query"]}, run_query)
server.add_tool("inspect_schema", "Get the database schema",
    {"type": "object", "properties": {}}, inspect_schema)

if __name__ == "__main__":
    # Ensure a dummy DB exists for the recipe
    if not Path(DB_PATH).exists():
        c = _connect()
        c.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT)")
        c.commit()
    server.run()
