# ROCLING 2026 一鍵重跑全部實驗（D2 + D5，E1/E2/E3 + 計分 + 錯誤分析）
# 用法：powershell -ExecutionPolicy Bypass -File scripts\run_all.ps1
# 前置：data/manifests/*.csv 已存在（否則先跑 scripts/prep/build_manifest.py）

$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)
$env:HF_HUB_OFFLINE = "1"   # D5 使用本機快取，避免網路中斷
$env:PYTHONUTF8 = "1"       # 避免 cp950 主控台編碼讓 print 失敗而漏句
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

function Step($name, $cmd) {
    Write-Host "`n========== $name ==========" -ForegroundColor Cyan
    Invoke-Expression $cmd
    if ($LASTEXITCODE -ne 0) { throw "$name failed (exit $LASTEXITCODE)" }
}

# 重跑前備份舊結果
if (Test-Path results) {
    $stamp = Get-Date -Format "yyyyMMdd_HHmmss"
    Copy-Item results "results_backup_$stamp" -Recurse
    Write-Host "已備份 results → results_backup_$stamp"
}

# ---------- E1 準確度 ----------
Step "E1 D2 mandarin (500)"  "python scripts/exp/run_lab_api.py e1 --testset mandarin  --manifest data/manifests/mandarin.csv"
Step "E1 D2 taiwanese (500)" "python scripts/exp/run_lab_api.py e1 --testset taiwanese --manifest data/manifests/taiwanese.csv"
Step "E1 D2 acp (50)"        "python scripts/exp/run_lab_api.py e1 --testset acp       --manifest data/manifests/acp.csv"
Step "E1 D5 mandarin (500)"  "python scripts/exp/run_d5.py e1 --testset mandarin --manifest data/manifests/mandarin.csv"
Step "E1 D5 acp (50)"        "python scripts/exp/run_d5.py e1 --testset acp      --manifest data/manifests/acp.csv"

# ---------- E3 幻覺 ----------
Step "E3 D2 (100)" "python scripts/exp/run_lab_api.py e3 --manifest data/manifests/hallucination.csv"
Step "E3 D5 (100)" "python scripts/exp/run_d5.py e3 --manifest data/manifests/hallucination.csv"

# ---------- E2 效能（國語 50 句） ----------
Remove-Item results/E2_performance.csv -ErrorAction SilentlyContinue
Step "E2 D2 API"    "python scripts/exp/run_lab_api.py e2 --manifest data/manifests/e2_latency_50.csv"
Step "E2 D5 GPU"    "python scripts/exp/run_d5.py e2 --manifest data/manifests/e2_latency_50.csv --device auto"
Step "E2 D5 CPU"    "python scripts/exp/run_d5.py e2 --manifest data/manifests/e2_latency_50.csv --device cpu"

# ---------- 計分與分析 ----------
Step "Score E1"        "python scripts/exp/score.py e1"
Step "Score E3"        "python scripts/exp/score.py e3"
Step "Error analysis"  "python scripts/exp/error_analysis.py"
Step "TW E1 analysis"  "python scripts/analysis/analyze_tw_e1.py"

Write-Host "`n全部完成。結果在 results/：E1_accuracy.csv、E2_performance.csv、E3_hallucination.csv、analysis/" -ForegroundColor Green
