# tool_handler.py
# Routes tool calls from Veda's brain to actual functions.

import re
from tools.web_search import search_web, fetch_page
from tools.filesystem import read_file, write_file, list_files, append_to_file
from memory.history import save_note, search_notes


def detect_and_execute_tool(ai_response: str) -> tuple[bool, str]:
    """
    Check if Veda wants to use a tool.
    
    Returns: (tool_used: bool, result: str)
    """

    # Veda uses TOOL: tool_name | PARAMS: params format
    # The brain's prompt specifies "TOOL: name | PARAMS: value" or similar
    
    tool_match = re.search(r'TOOL:\s*(\w+)', ai_response)
    params_match = re.search(r'PARAMS:\s*(.+?)(?:\n|$)', ai_response, re.DOTALL)

    if not tool_match:
        return False, ai_response

    tool_name = tool_match.group(1).strip()
    params = params_match.group(1).strip() if params_match else ""

    if tool_name == "search_web":
        return True, search_web(params)

    elif tool_name == "fetch_page":
        return True, fetch_page(params)

    elif tool_name == "read_file":
        return True, read_file(params)

    elif tool_name == "list_files":
        return True, list_files(params)

    elif tool_name == "write_file":
        if "|" in params:
            parts = params.split("|", 1)
            path = parts[0].strip()
            content = parts[1].strip()
            return True, write_file(path, content)
        return True, "Error: write_file requires 'path | content' parameters."

    elif tool_name == "save_note":
        if "|" in params:
            parts = params.split("|", 1)
            title = parts[0].strip()
            content = parts[1].strip()
            return True, save_note(title, content)
        return True, save_note("Quick Note", params)

    elif tool_name == "search_notes":
        notes = search_notes(params)
        if notes:
            formatted = "\n\n".join([f"**{n['title']}**: {n['content']}" for n in notes])
            return True, f"Found {len(notes)} relevant notes:\n\n{formatted}"
        return True, "No matching notes found."

    return True, f"Unknown tool: {tool_name}"
