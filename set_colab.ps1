# set_colab.ps1
# Update Veda's Ollama connection URL after Colab restarts

param (
    [string]$url
)

if (-not $url) {
    $url = Read-Host "Paste your new Cloudflare tunnel URL (e.g., https://xyz.trycloudflare.com)"
}

# Remove trailing slash
$url = $url.TrimEnd('/')

$configDir = Join-Path $PSScriptRoot "config"
if (-not (Test-Path $configDir)) {
    New-Item -ItemType Directory -Path $configDir | Out-Null
}

$urlFile = Join-Path $configDir "colab_url.txt"
$url | Out-File -FilePath $urlFile -Encoding utf8

Write-Host "`n✓ Veda will now connect to: $url" -ForegroundColor Green

# Test the connection
Write-Host "Testing connection..." -ForegroundColor Cyan
try {
    $response = Invoke-RestMethod -Uri "$url/api/tags" -Method Get -TimeoutSec 10
    Write-Host "✓ Connection successful!" -ForegroundColor Green
    Write-Host "Launch Veda with: ./launch.ps1" -ForegroundColor Yellow
} catch {
    Write-Host "✗ Cannot reach $url" -ForegroundColor Red
    Write-Host "  Make sure the Colab notebook is running and cloudflared tunnel is active." -ForegroundColor Yellow
}
