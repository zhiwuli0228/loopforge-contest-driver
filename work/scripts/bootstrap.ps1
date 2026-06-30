param(
    [string]$SourceRoot = ""
)

$ErrorActionPreference = "Stop"

$RootDir = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$RunScript = Join-Path $RootDir "work\scripts\run.ps1"

if ($SourceRoot -and $SourceRoot.Trim() -ne "") {
    powershell -ExecutionPolicy Bypass -File $RunScript -SourceRoot $SourceRoot
}
else {
    powershell -ExecutionPolicy Bypass -File $RunScript
}
