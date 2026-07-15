# 用 Windows 內建 OpenSSH scp 下載（比 Python paramiko 較不易認證失敗）
# 用法：
#   powershell -ExecutionPolicy Bypass -File scripts\download_corpus_scp.ps1
#   powershell -ExecutionPolicy Bypass -File scripts\download_corpus_scp.ps1 -Subset rocling -Dest "E:\data\22k_corpus"

param(
    [ValidateSet("rocling", "rocling-plus-zh", "tw", "tw-corpus", "metadata-only")]
    [string]$Subset = "rocling",
    [string]$Dest = "E:\data\22k_corpus",
    [string]$Host_ = "140.116.245.147",
    [int]$Port = 24680,
    [string]$User = "an4096750"
)

$ErrorActionPreference = "Stop"
$RemoteBase = "~/Linux_DATA/synthesis/corpus/corpus_manager/22k_corpus"

if (-not (Test-Path $Dest)) {
    New-Item -ItemType Directory -Path $Dest -Force | Out-Null
}

Write-Host "============================================================"
Write-Host "  SCP download -> $Dest"
Write-Host "  Server: ${User}@${Host_}:${Port}"
Write-Host "  Subset: $Subset"
Write-Host "============================================================"
Write-Host ""
Write-Host "接下來會多次詢問 SSH 密碼（每次 scp 一次）。"
Write-Host "若只想測試連線，先執行："
Write-Host "  ssh -p $Port ${User}@${Host_} `"echo OK`""
Write-Host ""

function Invoke-ScpDir($RemoteSub, $LocalName) {
    $localPath = Join-Path $Dest $LocalName
    $remote = "${User}@${Host_}:${RemoteBase}/${RemoteSub}"
    Write-Host ">> scp -P $Port -r $remote"
    Write-Host "   -> $localPath"
    & scp -P $Port -r $remote $localPath
    if ($LASTEXITCODE -ne 0) { throw "scp failed: $RemoteSub (exit $LASTEXITCODE)" }
}

function Invoke-ScpFile($RemoteSub, $LocalName) {
    $localPath = Join-Path $Dest $LocalName
    $remote = "${User}@${Host_}:${RemoteBase}/${RemoteSub}"
    Write-Host ">> scp -P $Port $remote"
    Write-Host "   -> $localPath"
    & scp -P $Port $remote $localPath
    if ($LASTEXITCODE -ne 0) { throw "scp failed: $RemoteSub (exit $LASTEXITCODE)" }
}

switch ($Subset) {
    "rocling" {
        Invoke-ScpDir "trandition_zh" "trandition_zh"
        Invoke-ScpDir "tw_clean" "tw_clean"
        Invoke-ScpFile "metadata.csv" "metadata.csv"
    }
    "rocling-plus-zh" {
        Invoke-ScpDir "trandition_zh" "trandition_zh"
        Invoke-ScpDir "tw_clean" "tw_clean"
        Invoke-ScpDir "zh" "zh"
        Invoke-ScpFile "metadata.csv" "metadata.csv"
    }
    "metadata-only" {
        Invoke-ScpFile "metadata.csv" "metadata.csv"
    }
    "tw" {
        Write-Host "警告: tw 整包約 200+ GB，請確認 E: 空間與時間。"
        Invoke-ScpDir "tw" "tw"
    }
    "tw-corpus" {
        Write-Host "下載 tw/corpus（台語 wav+文字，通常比整包 tw 小）"
        Invoke-ScpDir "tw/corpus" "tw/corpus"
    }
}

Write-Host ""
Write-Host "Done. Files at $Dest"
