param(
    [string]$WorkDir = (Split-Path -Parent $PSScriptRoot),
    [string]$CodeDir = (Join-Path (Split-Path -Parent (Split-Path -Parent $PSScriptRoot)) "code")
)

$ErrorActionPreference = "Stop"

# Bootstrap the LoopForge runner from the contest root.
# Override -WorkDir or -CodeDir only when testing an explicit alternate layout.

function Resolve-Python {
    $python = Get-Command python -ErrorAction SilentlyContinue
    if ($python) {
        return "python"
    }

    $py = Get-Command py -ErrorAction SilentlyContinue
    if ($py) {
        return "py -3"
    }

    throw "python interpreter not found"
}

$WorkDir = (Resolve-Path $WorkDir).Path
$RootDir = Split-Path -Parent $WorkDir
if (-not [System.IO.Path]::IsPathRooted($CodeDir)) {
    $CodeDir = Join-Path $RootDir $CodeDir
}

$PythonCmd = Resolve-Python
$RunnerPath = Join-Path $WorkDir "runtime/loopforge_runner.py"
$CodingSkillPath = Join-Path $WorkDir "skills/code-implementation/SKILL.md"
$CodingSkillReady = Test-Path $CodingSkillPath

Write-Host "Coding skill: work/skills/code-implementation/SKILL.md"
Write-Host ("Coding skill ready: " + ($(if ($CodingSkillReady) { "yes" } else { "no" })))

Invoke-Expression "$PythonCmd `"$RunnerPath`" --work-dir `"$WorkDir`" --code-dir `"$CodeDir`" --init --self-check --detect"
