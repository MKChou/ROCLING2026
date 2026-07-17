# ROCLING 2026 實驗室環境架設（Windows PowerShell）
# 用法：在專案根目錄執行
#   powershell -ExecutionPolicy Bypass -File scripts\setup_env.ps1

$ErrorActionPreference = "Stop"
$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
Set-Location $ProjectRoot

Write-Host "========================================" -ForegroundColor Cyan
Write-Host " ROCLING 2026 Lab Environment Setup" -ForegroundColor Cyan
Write-Host " Project: $ProjectRoot" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# 1. ffmpeg
if (-not (Get-Command ffmpeg -ErrorAction SilentlyContinue)) {
    Write-Host "[!] ffmpeg not found. Installing via winget..." -ForegroundColor Yellow
    winget install Gyan.FFmpeg --accept-package-agreements --accept-source-agreements
} else {
    Write-Host "[OK] ffmpeg: $(ffmpeg -version 2>&1 | Select-Object -First 1)" -ForegroundColor Green
}

# 2. Python venv
$VenvPath = Join-Path $ProjectRoot ".venv"
if (-not (Test-Path $VenvPath)) {
    Write-Host "Creating venv at .venv ..." -ForegroundColor Yellow
    python -m venv $VenvPath
}
$Python = Join-Path $VenvPath "Scripts\python.exe"
$Pip = Join-Path $VenvPath "Scripts\pip.exe"
Write-Host "[OK] venv: $Python" -ForegroundColor Green

# 3. Install dependencies
Write-Host "Installing requirements (may take several minutes)..." -ForegroundColor Yellow
& $Pip install --upgrade pip
& $Pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) {
    Write-Host "[!] venv pip install failed (network?). Using system Python if packages exist." -ForegroundColor Yellow
    Write-Host "    Re-run later: .\.venv\Scripts\pip install -r requirements.txt" -ForegroundColor Yellow
    $Python = "python"
}

# 4. Normalize ACP wavs (legacy pilot)
Write-Host "Normalizing legacy ACP recordings to 16kHz mono..." -ForegroundColor Yellow
& $Python scripts\prep\convert_acp_wavs.py

# 5. Pre-download Nemotron model
Write-Host "Pre-loading Nemotron model (first run downloads ~2.5GB)..." -ForegroundColor Yellow
& $Python scripts\env\verify_env.py

Write-Host ""
Write-Host "Setup complete. Activate venv:" -ForegroundColor Green
Write-Host "  .\.venv\Scripts\Activate.ps1" -ForegroundColor White
Write-Host ""
Write-Host "Run experiments:" -ForegroundColor Green
Write-Host "  python scripts\run_d5.py e1 --testset acp --manifest data\manifests\acp.csv" -ForegroundColor White
Write-Host "  python scripts\score.py e1 --profile D5" -ForegroundColor White
