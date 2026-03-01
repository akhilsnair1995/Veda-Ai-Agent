# mcp/servers/memory_server.py
import sys
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR))
from mcp.server_base import MCPServer

# We'll import SemanticMemory if possible, otherwise we stub it out using direct ChromaDB connection
try:
    from memory.semantic import SemanticMemory
    semantic = SemanticMemory()
except ImportError:
    # Fallback if module pathing is tricky during raw testing
    semantic = None

# We use a dedicated facts db
FACTS_DB = BASE_DIR / "memory" / "facts.db"

def _init_db():
    if not FACTS_DB.parent.exists():
        FACTS_DB.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(FACTS_DB)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS facts
                 (key TEXT PRIMARY KEY, value TEXT, category TEXT, active INTEGER DEFAULT 1)''')
    conn.commit()
    conn.close()

_init_db()

server = MCPServer(name="memory", version="1.0.0")

def store_memory(text: str, category: str = "general", tags: str = "") -> str:
    if semantic:
        semantic.store(text, metadata={"category": category, "tags": tags})
        return "Stored in semantic memory."
    return "Semantic memory module not loaded."

def search_memory(query: str, top_k: int = 3) -> str:
    if semantic:
        results = semantic.search(query, top_k=top_k)
        return "\n---\n".join(results) if results else "No semantic memories found."
    return "Semantic memory module not loaded."

def store_fact(key: str, value: str, category: str = "general") -> str:
    conn = sqlite3.connect(FACTS_DB)
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO facts (key, value, category, active) VALUES (?, ?, ?, 1)", (key, value, category))
    conn.commit()
    conn.close()
    return f"Stored fact: {key}."

def get_fact(key: str) -> str:
    conn = sqlite3.connect(FACTS_DB)
    c = conn.cursor()
    c.execute("SELECT value FROM facts WHERE key = ? AND active = 1", (key,))
    res = c.fetchone()
    conn.close()
    return res[0] if res else f"Fact '{key}' not found."

def list_facts(category: str = None) -> str:
    conn = sqlite3.connect(FACTS_DB)
    c = conn.cursor()
    if category:
        c.execute("SELECT key, value FROM facts WHERE category = ? AND active = 1", (category,))
    else:
        c.execute("SELECT key, value FROM facts WHERE active = 1")
    res = c.fetchall()
    conn.close()
    if not res: return "No facts found."
    return "\n".join([f"{k}: {v}" for k, v in res])

def forget(query: str) -> str:
    # Disable facts matching query
    conn = sqlite3.connect(FACTS_DB)
    c = conn.cursor()
    c.execute("UPDATE facts SET active = 0 WHERE key LIKE ?", (f"%{query}%",))
    count = c.rowcount
    conn.commit()
    conn.close()
    return f"Forgot {count} facts."

def memory_stats() -> str:
    conn = sqlite3.connect(FACTS_DB)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM facts WHERE active = 1")
    count = c.fetchone()[0]
    conn.close()
    
    sem_stat = "Active" if semantic else "Inactive"
    return f"Semantic DB: {sem_stat}\nDiscrete Facts: {count}"

# Resources
def res_facts():
    return list_facts()

def res_stats():
    return memory_stats()

server.add_tool("store_memory", "Store unstructured memory",
    {"type": "object", "properties": {"text": {"type": "string"}, "category": {"type": "string"}, "tags": {"type": "string"}}, "required": ["text"]}, store_memory)
server.add_tool("search_memory", "Search semantic memory",
    {"type": "object", "properties": {"query": {"type": "string"}, "top_k": {"type": "integer"}}, "required": ["query"]}, search_memory)
server.add_tool("store_fact", "Store a discrete key-value fact",
    {"type": "object", "properties": {"key": {"type": "string"}, "value": {"type": "string"}, "category": {"type": "string"}}, "required": ["key", "value"]}, store_fact)
server.add_tool("get_fact", "Get a fact by key",
    {"type": "object", "properties": {"key": {"type": "string"}}, "required": ["key"]}, get_fact)
server.add_tool("list_facts", "List all facts",
    {"type": "object", "properties": {"category": {"type": "string"}}}, list_facts)
server.add_tool("forget", "Mark a fact as forgotten",
    {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}, forget)
server.add_tool("memory_stats", "Get memory statistics",
    {"type": "object", "properties": {}}, memory_stats)

server.add_resource("memory://facts", "All Facts", "Dump of all facts", res_facts)
server.add_resource("memory://stats", "Memory Stats", "System stats", res_stats)

if __name__ == "__main__":
    server.run()
