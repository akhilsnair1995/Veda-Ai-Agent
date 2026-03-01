# mcp/servers/web_server.py
import sys
import requests
import json
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR))
from mcp.server_base import MCPServer

server = MCPServer(name="web", version="1.0.0")

def search(query: str, max_results: int = 5) -> str:
    try:
        results = []
        with DDGS() as ddgs:
            results_gen = ddgs.text(query, max_results=max_results)
            if results_gen:
                results = list(results_gen)
        
        if not results:
            return "No results found."
            
        formatted = []
        for r in results:
            formatted.append(f"Title: {r['title']}\nURL: {r['href']}\nSnippet: {r['body']}\n---")
        return "\n".join(formatted)
    except Exception as e:
        return f"Search error: {e}"

def fetch_page(url: str, extract_text: bool = True) -> str:
    try:
        response = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
        response.raise_for_status()
        if not extract_text:
            return response.text[:5000] # Return raw HTML snippet
        soup = BeautifulSoup(response.text, 'html.parser')
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.extract()
        text = soup.get_text(separator='\n', strip=True)
        return text[:10000] # Return truncated text to prevent overflow
    except Exception as e:
        return f"Fetch error: {e}"

def fetch_json(url: str, headers: dict = None) -> str:
    try:
        response = requests.get(url, headers=headers or {}, timeout=15)
        response.raise_for_status()
        return json.dumps(response.json(), indent=2)[:5000]
    except Exception as e:
        return f"API fetch error: {e}"

def download_file(url: str, save_path: str) -> str:
    try:
        p = Path(save_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()
        with p.open('wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        return f"Successfully downloaded to {save_path}"
    except Exception as e:
        return f"Download error: {e}"

def check_url(url: str) -> str:
    try:
        response = requests.head(url, timeout=5)
        return f"Status Code: {response.status_code}\nAccessible: {response.ok}"
    except Exception as e:
        return f"URL check failed: {e}"

def extract_links(url: str) -> str:
    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        links = []
        for a in soup.find_all('a', href=True):
            links.append(f"{a.text.strip()}: {a['href']}")
        return "\n".join(links[:50]) # Top 50
    except Exception as e:
        return f"Link extraction error: {e}"

def summarize_page(url: str) -> str:
    text = fetch_page(url)
    if text.startswith("Fetch error"): return text
    return f"[Fetched content length: {len(text)} characters. Use brain to summarize.]\nContent:\n" + text[:3000]

server.add_tool("search", "Search DuckDuckGo",
    {"type": "object", "properties": {"query": {"type": "string"}, "max_results": {"type": "integer"}}, "required": ["query"]}, search)
server.add_tool("fetch_page", "Fetch and extract text from a webpage",
    {"type": "object", "properties": {"url": {"type": "string"}, "extract_text": {"type": "boolean"}}, "required": ["url"]}, fetch_page)
server.add_tool("fetch_json", "Fetch JSON from an API",
    {"type": "object", "properties": {"url": {"type": "string"}, "headers": {"type": "object"}}, "required": ["url"]}, fetch_json)
server.add_tool("download_file", "Download a file from URL",
    {"type": "object", "properties": {"url": {"type": "string"}, "save_path": {"type": "string"}}, "required": ["url", "save_path"]}, download_file)
server.add_tool("check_url", "Check if a URL is accessible",
    {"type": "object", "properties": {"url": {"type": "string"}}, "required": ["url"]}, check_url)
server.add_tool("extract_links", "Extract links from a page",
    {"type": "object", "properties": {"url": {"type": "string"}}, "required": ["url"]}, extract_links)
server.add_tool("summarize_page", "Fetch a page to be summarized",
    {"type": "object", "properties": {"url": {"type": "string"}}, "required": ["url"]}, summarize_page)

if __name__ == "__main__":
    server.run()
