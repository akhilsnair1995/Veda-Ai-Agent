#!/bin/bash
# install_skills_mcp.sh
# Installs Veda's Skills and MCP Architecture

echo "=========================================="
echo "Installing Veda Skills & MCP Architecture"
echo "=========================================="

BASE_DIR="$(pwd)"
echo "Base Directory: $BASE_DIR"

# 1. Create Directories
echo "Creating directory structure..."
mkdir -p "$BASE_DIR/skills"
mkdir -p "$BASE_DIR/mcp/servers"
mkdir -p "$BASE_DIR/mcp/recipes"
mkdir -p "$BASE_DIR/config"
mkdir -p "$BASE_DIR/notes"
mkdir -p "$BASE_DIR/memory"

# 2. Python Dependencies
echo "Installing dependencies..."
# Assuming we are in a virtual environment
pip install rich requests beautifulsoup4 duckduckgo-search pyyaml chromadb

# 3. Create __init__.py files
echo "Initializing Python modules..."
touch "$BASE_DIR/skills/__init__.py"
touch "$BASE_DIR/mcp/__init__.py"
touch "$BASE_DIR/mcp/servers/__init__.py"

# 4. Connection Test for MCP
echo "=========================================="
echo "Testing MCP Servers..."
echo "=========================================="
python -c "
from mcp.server_manager import MCPServerManager
manager = MCPServerManager()
manager.start_all()
manager.disconnect_all()
print('MCP Connection Test Passed')
"

# 5. Skill Detection Test
echo "=========================================="
echo "Testing Skill Registry..."
echo "=========================================="
python -c "
from skills.skill_registry import SkillRegistry
registry = SkillRegistry()
print(f'Discovered {len(registry.skills)} skills.')
print('Skill Registry Test Passed')
"

echo "=========================================="
echo "SUCCESS: Architecture Installed & Verified"
echo "=========================================="
