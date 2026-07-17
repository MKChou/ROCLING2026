# ACP-DRP C3／C4 probe — 獨立 tag，不覆蓋舊 E3 pilot
# 用法：powershell -ExecutionPolicy Bypass -File scripts\run_c3_c4.ps1

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

$env:PYTHONUNBUFFERED = "1"
$env:PYTHONUTF8 = "1"
$env:HF_HUB_OFFLINE = "1"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$Manifest = "data/manifests/c3_c4.csv"
$Tag = "c3_c4"
$Py = if (Test-Path ".venv\Scripts\python.exe") { ".venv\Scripts\python.exe" } else { "python" }

function Invoke-Step($name, [scriptblock]$block) {
    Write-Host "`n========== $name ==========" -ForegroundColor Cyan
    & $block
    if ($LASTEXITCODE -ne 0) { throw "$name failed (exit $LASTEXITCODE)" }
}

if (-not (Test-Path -LiteralPath $Manifest)) {
    throw "Missing manifest: $Manifest (merge c3_short + c4_hesitation first)"
}
$rows = @(Import-Csv -LiteralPath $Manifest)
if ($rows.Count -ne 200) {
    throw "Expected 200 rows (C3 100 + C4 100), got $($rows.Count)"
}

Write-Host "=== C3/C4 probe ($Tag) ===" -ForegroundColor Cyan
Write-Host "Manifest: $Manifest ($($rows.Count) clips)"

Invoke-Step "D2 lang-med" { & $Py scripts/exp/run_lab_api.py e3 --manifest $Manifest --profile D2 --tag $Tag }
Invoke-Step "D2 lang-base" { & $Py scripts/exp/run_lab_api.py e3 --manifest $Manifest --profile D2_Llegacy --tag $Tag --lang "Chinese & Taiwanese" }
Invoke-Step "D5" { & $Py scripts/exp/run_d5.py e3 --manifest $Manifest --device auto --tag $Tag }
Invoke-Step "D5+VAD" { & $Py scripts/exp/run_d5.py e3 --manifest $Manifest --device auto --vad --tag $Tag }
Invoke-Step "WspPublic" { & $Py scripts/exp/run_whisper.py e3 --manifest $Manifest --device auto --tag $Tag }
Invoke-Step "WspPublic+VAD" { & $Py scripts/exp/run_whisper.py e3 --manifest $Manifest --device auto --vad --tag $Tag }

Invoke-Step "Score" { & $Py scripts/exp/score.py e3 --tag $Tag }
Invoke-Step "Summarize" { & $Py scripts/analysis/summarize_e3.py --tag $Tag }
Invoke-Step "Compare" { & $Py scripts/analysis/compare_e3_profiles.py --tag $Tag }

Write-Host "`n=== Done ===" -ForegroundColor Green
Write-Host "JSONL: results\E3_outputs\*_c3_c4.jsonl"
Write-Host "Scores: results\E3_c3_c4.csv"
Write-Host "Compare: results\analysis\e3_c3_c4_compare.csv"
