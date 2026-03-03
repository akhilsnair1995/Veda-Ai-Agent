# mcp/servers/google_apps_server.py
import os
import sys
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR))
from mcp.server_base import MCPServer

server = MCPServer(name="google_apps", version="1.0.0")

# Note: This requires google-api-python-client, google-auth-httplib2, google-auth-oauthlib
# For a production agent, these should be pre-installed and authenticated.

def check_auth() -> bool:
    """Verify if Google API credentials exist."""
    creds_path = Path.home() / ".gemini" / "oauth_creds.json"
    return creds_path.exists()

def gmail_list_recent(max_results: int = 10) -> str:
    """List recent email subjects and snippets."""
    if not check_auth():
        return "Error: Google credentials not found. Run authentication setup first."
    return "[MOCK] Gmail: 1. Project Update - Subject: HVAC load calculations ready
2. Meeting Invite - Subject: Weekly Sync"

def drive_search(query: str) -> str:
    """Search for files in Google Drive."""
    if not check_auth():
        return "Error: Google credentials not found."
    return f"[MOCK] Google Drive search for '{query}':
1. {query}_V1.pdf
2. {query}_Notes.docx"

def calendar_list_events() -> str:
    """List upcoming calendar events."""
    if not check_auth():
        return "Error: Google credentials not found."
    return "[MOCK] Calendar: 1. Design Review - 14:00 today
2. Client Call - 10:00 tomorrow"

def sheets_read_range(spreadsheet_id: str, range_name: str) -> str:
    """Read data from a Google Sheet."""
    return f"[MOCK] Sheet {spreadsheet_id} range {range_name}: [[Name, Age], [Akhil, 30], [Veda, 1]]"

server.add_tool("gmail_list_recent", "Get recent emails from Gmail",
    {"type": "object", "properties": {"max_results": {"type": "integer"}}}, gmail_list_recent)

server.add_tool("drive_search", "Search for files in Google Drive",
    {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}, drive_search)

server.add_tool("calendar_list_events", "Get upcoming calendar events",
    {"type": "object", "properties": {}}, calendar_list_events)

server.add_tool("sheets_read_range", "Read a range of cells from a spreadsheet",
    {
        "type": "object", 
        "properties": {
            "spreadsheet_id": {"type": "string"},
            "range_name": {"type": "string"}
        }, 
        "required": ["spreadsheet_id", "range_name"]
    }, sheets_read_range)

if __name__ == "__main__":
    server.run()
