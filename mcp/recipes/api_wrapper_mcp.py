# mcp/recipes/api_wrapper_mcp.py
# RECIPE 2 — API WRAPPER MCP SERVER
# Wraps a REST API as an MCP server.
# Example: Wrapping the GitHub API

import os
import requests
import json
from mcp.server_base import MCPServer

server = MCPServer(name="github_api", version="1.0.0")

# Setup auth
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
headers = {
    "Accept": "application/vnd.github.v3+json",
    "Authorization": f"token {GITHUB_TOKEN}" if GITHUB_TOKEN else ""
}

def get_user_profile(username: str) -> str:
    """Fetch a GitHub user profile."""
    url = f"https://api.github.com/users/{username}"
    try:
        resp = requests.get(url, headers=headers)
        resp.raise_for_status()
        data = resp.json()
        return f"User: {data.get('login')}
Name: {data.get('name')}
Bio: {data.get('bio')}
Followers: {data.get('followers')}"
    except Exception as e:
        return f"API Error: {e}"

def list_repos(username: str) -> str:
    """List public repositories for a user."""
    url = f"https://api.github.com/users/{username}/repos?sort=updated&per_page=5"
    try:
        resp = requests.get(url, headers=headers)
        resp.raise_for_status()
        repos = resp.json()
        result = []
        for r in repos:
            result.append(f"{r.get('name')} - Stars: {r.get('stargazers_count')} - {r.get('description')}")
        return "
".join(result)
    except Exception as e:
        return f"API Error: {e}"

server.add_tool("get_user_profile", "Get GitHub profile info",
    {"type": "object", "properties": {"username": {"type": "string"}}, "required": ["username"]}, get_user_profile)
server.add_tool("list_repos", "List top 5 recent GitHub repos",
    {"type": "object", "properties": {"username": {"type": "string"}}, "required": ["username"]}, list_repos)

if __name__ == "__main__":
    server.run()
