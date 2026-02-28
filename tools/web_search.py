# tools/web_search.py
# Lets the chatbot search the web using DuckDuckGo.
# No API key needed. Completely free and private.

from duckduckgo_search import DDGS
import requests
from bs4 import BeautifulSoup


def search_web(query: str, max_results: int = 5) -> str:
    """
    Search the web for a query and return summarized results.
    
    Example: search_web("latest Python 3.13 features")
    Returns a formatted string of search results.
    """
    try:
        results = []
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=max_results):
                results.append(f"Title: {r['title']}\nURL: {r['href']}\nSummary: {r['body']}\n")

        if not results:
            return "No search results found."

        return "WEB SEARCH RESULTS:\n\n" + "\n---\n".join(results)

    except Exception as e:
        return f"Web search failed: {e}"


def fetch_page(url: str) -> str:
    """
    Fetch and read the text content of a web page.
    Useful when you want the full content of a specific page.
    
    Example: fetch_page("https://docs.python.org/3/")
    """
    try:
        headers = {"User-Agent": "Mozilla/5.0 (compatible; Veda/1.0)"}
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")

        # Remove scripts and styles (we only want readable text)
        for tag in soup(["script", "style", "nav", "footer"]):
            tag.decompose()

        text = soup.get_text(separator="\n", strip=True)

        # Limit to first 3000 characters to avoid overwhelming the AI
        return text[:3000] + ("...[truncated]" if len(text) > 3000 else "")

    except Exception as e:
        return f"Could not fetch page: {e}"
