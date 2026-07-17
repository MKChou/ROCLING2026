# ACP-DRP C1 silence probe — 獨立 tag，不覆蓋舊 E3
# 用法：powershell -ExecutionPolicy Bypass -File scripts\run_c1_silence.ps1

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

$Manifest = "data/manifests/c1_silence.csv"
$Tag = "c1_silence"
$Py = if (Test-Path ".venv\Scripts\python.exe") { ".venv\Scripts\python.exe" } else { "python" }

Write-Host "=== C1 silence probe ($Tag) ===" -ForegroundColor Cyan
Write-Host "Manifest: $Manifest"

# 1) Cloud D2 lang-med
& $Py scripts/exp/run_lab_api.py e3 --manifest $Manifest --profile D2 --tag $Tag
# 2) Cloud D2 lang-base
& $Py scripts/exp/run_lab_api.py e3 --manifest $Manifest --profile D2_Llegacy --tag $Tag --lang "Chinese & Taiwanese"

# 3-4) Edge Nemotron ± VAD
& $Py scripts/exp/run_d5.py e3 --manifest $Manifest --device auto --tag $Tag
& $Py scripts/exp/run_d5.py e3 --manifest $Manifest --device auto --vad --tag $Tag

# 5-6) Public Whisper ± VAD
& $Py scripts/exp/run_whisper.py e3 --manifest $Manifest --device auto --tag $Tag
& $Py scripts/exp/run_whisper.py e3 --manifest $Manifest --device auto --vad --tag $Tag

# Score
& $Py scripts/exp/score.py e3 --tag $Tag

Write-Host "=== Done. See results/E3_c1_silence.csv ===" -ForegroundColor Green
