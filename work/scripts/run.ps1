param(
    [string]$SourceRoot = ""
)

$ErrorActionPreference = "Stop"

$RootDir = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$WorkDir = Join-Path $RootDir "work"
$ResultDir = Join-Path $RootDir "result"
$LogDir = Join-Path $RootDir "logs"

if (-not $SourceRoot -or $SourceRoot.Trim() -eq "") {
    $SourceRoot = ""
}

New-Item -ItemType Directory -Force -Path (Join-Path $ResultDir "issues") | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $LogDir "trace") | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $LogDir "trace\c-to-rust") | Out-Null
if (-not (Test-Path (Join-Path $LogDir "interaction.md"))) {
    Set-Content -Path (Join-Path $LogDir "interaction.md") -Value "# Interaction Log`r`n`r`nNo manual interaction.`r`n"
}

$RunnerArgs = @()
if ($SourceRoot -and $SourceRoot.Trim() -ne "") {
    $RunnerArgs = @("--source-root", $SourceRoot)
} elseif ($env:SOURCE_ROOT -and $env:SOURCE_ROOT.Trim() -ne "") {
    $RunnerArgs = @("--source-root", $env:SOURCE_ROOT)
} else {
    $FallbackCandidates = @(
        (Join-Path $RootDir ".code\source-project"),
        (Join-Path $RootDir "work\code\source-project"),
        (Join-Path $RootDir "code\source-project")
    )
    foreach ($FallbackRoot in $FallbackCandidates) {
        if (Test-Path $FallbackRoot) {
            $RunnerArgs = @("--source-root", $FallbackRoot)
            break
        }
    }
    if (-not $RunnerArgs) {
        $RunnerArgs = @()
    }
}

& python (Join-Path $WorkDir "runtime\loopforge_runner.py") `
  --work-dir $WorkDir `
  --result-dir $ResultDir `
  --log-dir $LogDir `
  @RunnerArgs `
  --run
