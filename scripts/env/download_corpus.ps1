# 下載實驗室 22k 語料到 E:\data\22k_corpus
# 用法（在 ROCLING2026 根目錄）：
#   powershell -ExecutionPolicy Bypass -File scripts\download_corpus.ps1
#   powershell -ExecutionPolicy Bypass -File scripts\download_corpus.ps1 -Subset rocling-plus-zh

param(
    [ValidateSet("rocling", "rocling-plus-zh", "full")]
    [string]$Subset = "rocling",
    [string]$Dest = "E:\data\22k_corpus"
)

$ErrorActionPreference = "Stop"
if (-not (Test-Path $Dest)) { New-Item -ItemType Directory -Path $Dest -Force | Out-Null }

if (-not $env:LAB_SSH_PASSWORD) {
    $secure = Read-Host "SSH password (an4096750@140.116.245.147:24680)" -AsSecureString
    $ptr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
    $env:LAB_SSH_PASSWORD = [Runtime.InteropServices.Marshal]::PtrToStringAuto($ptr)
}

$env:ROCLING_CORPUS_ROOT = $Dest
Set-Location $PSScriptRoot\..

Write-Host "Downloading subset=$Subset -> $Dest"
Write-Host "Estimated: rocling ~139GB | rocling-plus-zh ~332GB | full ~550GB+"
Write-Host ""

python scripts\download_corpus.py --subset $Subset --dest $Dest
