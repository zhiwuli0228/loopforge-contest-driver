param(
    [string]$SourceRoot = ""
)

$ErrorActionPreference = "Stop"

$RootDir = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$WorkDir = Join-Path $RootDir "work"
$ResultDir = Join-Path $RootDir "result"
$LogDir = Join-Path $RootDir "logs"

if ($SourceRoot -and $SourceRoot.Trim() -ne "") {
    $env:SOURCE_ROOT = $SourceRoot
}
elseif (-not $env:SOURCE_ROOT -or $env:SOURCE_ROOT.Trim() -eq "") {
    $env:SOURCE_ROOT = "code"
}

New-Item -ItemType Directory -Force -Path (Join-Path $ResultDir "issues") | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $LogDir "trace") | Out-Null
if (-not (Test-Path (Join-Path $LogDir "interaction.md"))) {
    Set-Content -Path (Join-Path $LogDir "interaction.md") -Value "# Interaction Log`r`n`r`nNo manual interaction.`r`n"
}

python (Join-Path $WorkDir "runtime\loopforge_runner.py") `
  --work-dir $WorkDir `
  --source-root $env:SOURCE_ROOT `
  --result-dir $ResultDir `
  --log-dir $LogDir `
  --run
