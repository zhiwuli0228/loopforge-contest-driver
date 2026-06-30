param(
    [string]$SourceRoot = ""
)

$ErrorActionPreference = "Stop"

$RootDir = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$WorkDir = Join-Path $RootDir "work"
$ResultDir = Join-Path $RootDir "result"
$LogDir = Join-Path $RootDir "logs"

New-Item -ItemType Directory -Force -Path (Join-Path $ResultDir "issues") | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $LogDir "trace") | Out-Null
if (-not (Test-Path (Join-Path $LogDir "interaction.md"))) {
    Set-Content -Path (Join-Path $LogDir "interaction.md") -Value "# Interaction Log`r`n`r`nNo manual interaction.`r`n"
}

if ($SourceRoot -and $SourceRoot.Trim() -ne "") {
    $RunnerArgs = @("--source-root", $SourceRoot)
}
else {
    $RunnerArgs = @()
}

python (Join-Path $WorkDir "runtime\loopforge_runner.py") `
  --work-dir $WorkDir `
  --result-dir $ResultDir `
  --log-dir $LogDir `
  @RunnerArgs `
  --run
