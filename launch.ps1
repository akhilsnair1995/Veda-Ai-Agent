param(
    [switch]$Web
)

$SCRIPT_DIR = $PSScriptRoot
Set-Location $SCRIPT_DIR

if ($Web) {
    Write-Host "`n--- Starting Veda Web Hub (Streamlit) ---" -ForegroundColor Cyan
} else {
    Write-Host "`n--- Starting Veda Intelligence (Windows Native) ---" -ForegroundColor Cyan
}

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
if (!($installed -match "rich") -or !($installed -match "openai") -or !($installed -match "duckduckgo-search") -or !($installed -match "streamlit") -or !($installed -match "pillow")) {
    Write-Host "Installing full Veda toolset..." -ForegroundColor Yellow
    pip install rich openai click python-dotenv chromadb duckduckgo-search requests beautifulsoup4 streamlit pillow
}

# 4. Check for .env file
if (!(Test-Path ".env")) {
    Write-Host "Creating default .env file..." -ForegroundColor Yellow
    "OPENAI_BASE_URL=http://localhost:1234/v1" | Out-File -FilePath ".env" -Encoding utf8
}

# 5. Start Veda with GPU Optimization
Write-Host "System: READY. Forcing Dedicated AMD GPU (Vulkan)..." -ForegroundColor Green
$env:HIP_VISIBLE_DEVICES="1"
$env:OLLAMA_VULKAN="1"
$env:HSA_OVERRIDE_GFX_VERSION="10.3.0"
$env:PYTHONUTF8="1"
$env:PYTHONIOENCODING="utf-8"

if ($Web) {
    streamlit run veda_desktop.py
} else {
    python chat.py
}
