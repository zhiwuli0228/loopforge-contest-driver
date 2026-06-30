param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$ArgsList
)

$ErrorActionPreference = "Stop"

$RunScript = Join-Path $PSScriptRoot "run.ps1"
powershell -ExecutionPolicy Bypass -File $RunScript @ArgsList
