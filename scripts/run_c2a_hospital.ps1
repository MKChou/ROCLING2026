param(
    [ValidateSet("auto", "cpu", "cuda")]
    [string]$Device = "cuda",
    [switch]$ValidateOnly,
    [switch]$IncludeLabApi,
    [string]$LabProfile = "D2",
    [string]$LabLang = ""
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$Manifest = Join-Path $ProjectRoot "data\manifests\c2a_hospital.csv"
$Tag = "c2a_hospital"

Set-Location $ProjectRoot

function Invoke-Python {
    param([Parameter(ValueFromRemainingArguments = $true)][string[]]$Arguments)
    & python @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Python command failed (exit $LASTEXITCODE): python $($Arguments -join ' ')"
    }
}

Write-Host "=== Validate C2A manifest ===" -ForegroundColor Cyan
if (-not (Test-Path -LiteralPath $Manifest -PathType Leaf)) {
    throw "Missing manifest: $Manifest"
}
$rows = @(Import-Csv -LiteralPath $Manifest)
if ($rows.Count -ne 100) {
    throw "Expected 100 manifest rows, got $($rows.Count)"
}
if (@($rows | Where-Object { $_.condition -ne "C2A" }).Count -gt 0) {
    throw "Manifest contains a condition other than C2A"
}
$venueGroups = @($rows | Group-Object venue)
if ($venueGroups.Count -ne 5 -or @($venueGroups | Where-Object { $_.Count -ne 20 }).Count -gt 0) {
    $counts = ($venueGroups | ForEach-Object { "$($_.Name)=$($_.Count)" }) -join ", "
    throw "Expected five venues with 20 clips each; got $counts"
}
$manifestDir = Split-Path -Parent $Manifest
foreach ($row in $rows) {
    $audio = [IO.Path]::GetFullPath((Join-Path $manifestDir $row.audio_path))
    if (-not (Test-Path -LiteralPath $audio -PathType Leaf)) {
        throw "Missing audio: $audio"
    }
}
$venueCounts = ($venueGroups | ForEach-Object { "$($_.Name)=$($_.Count)" }) -join ", "
Write-Host "C2A ready: 100 clips; $venueCounts" -ForegroundColor Green

if ($ValidateOnly) {
    Write-Host "Validation complete; experiments were not started." -ForegroundColor Green
    return
}

Write-Host "`n=== D5 (without VAD) ===" -ForegroundColor Cyan
Invoke-Python scripts/exp/run_d5.py e3 --manifest $Manifest --device $Device --tag $Tag

Write-Host "`n=== D5 (Silero VAD 0.5) ===" -ForegroundColor Cyan
Invoke-Python scripts/exp/run_d5.py e3 --manifest $Manifest --device $Device --vad --tag $Tag

Write-Host "`n=== Public Whisper (without VAD) ===" -ForegroundColor Cyan
Invoke-Python scripts/exp/run_whisper.py e3 --manifest $Manifest --device $Device --tag $Tag

Write-Host "`n=== Public Whisper (Silero VAD 0.5) ===" -ForegroundColor Cyan
Invoke-Python scripts/exp/run_whisper.py e3 --manifest $Manifest --device $Device --vad --tag $Tag

if ($IncludeLabApi) {
    Write-Host "`n=== Lab API ===" -ForegroundColor Yellow
    $apiArgs = @(
        "scripts/exp/run_lab_api.py", "e3",
        "--manifest", $Manifest,
        "--profile", $LabProfile,
        "--tag", $Tag
    )
    if ($LabLang) {
        $apiArgs += @("--lang", $LabLang)
    }
    Invoke-Python @apiArgs
} else {
    Write-Host "`nLab API skipped. Add -IncludeLabApi only after confirming data-use permission." -ForegroundColor Yellow
}

Write-Host "`n=== Score and summarize ===" -ForegroundColor Cyan
Invoke-Python scripts/exp/score.py e3 --tag $Tag
Invoke-Python scripts/analysis/summarize_e3.py --tag $Tag
Invoke-Python scripts/analysis/compare_e3_profiles.py --tag $Tag

Write-Host "`n=== Done ===" -ForegroundColor Green
Write-Host "JSONL: results\E3_outputs\*_$Tag.jsonl"
Write-Host "Scores: results\E3_$Tag.csv"
Write-Host "Compare: results\analysis\e3_${Tag}_compare.csv"
