# launch.ps1
# Windows PowerShell Launch Script for Veda Agent

$SCRIPT_DIR = $PSScriptRoot
Set-Location $SCRIPT_DIR

Write-Host "`n--- Starting Veda Intelligence (Windows Native) ---" -ForegroundColor Cyan

# 1. Check for Python
if (!(Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "Error: Python not found. Please install Python 3.10+." -ForegroundColor Red
    exit
}

# 2. Setup Virtual Environment
if (!(Test-Path "venv_win")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv venv_win
}

# 3. Activate and Install Dependencies
Write-Host "Activating environment..." -ForegroundColor Yellow
& ".\venv_win\Scripts\Activate.ps1"

# Check if essential packages are installed
$installed = pip list
if (!($installed -match "rich") -or !($installed -match "ollama") -or !($installed -match "duckduckgo-search")) {
    Write-Host "Installing full Veda toolset..." -ForegroundColor Yellow
    pip install rich ollama click python-dotenv chromadb duckduckgo-search requests beautifulsoup4
}

# 4. Check for .env file
if (!(Test-Path ".env")) {
    Write-Host "Creating default .env file..." -ForegroundColor Yellow
    "OLLAMA_HOST=http://localhost:11434" | Out-File -FilePath ".env" -Encoding utf8
}

# 5. Start Veda with GPU Optimization
Write-Host "System: READY. Forcing Dedicated AMD GPU (Vulkan)..." -ForegroundColor Green
$env:HIP_VISIBLE_DEVICES="1"
$env:OLLAMA_VULKAN="1"
$env:HSA_OVERRIDE_GFX_VERSION="10.3.0"
python chat.py
