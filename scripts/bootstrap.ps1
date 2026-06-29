param(
    [string]$WorkDir = ".",
    [string]$CodeDir = "code"
)

$ErrorActionPreference = "Stop"

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

$PythonCmd = Resolve-Python
$RunnerPath = Join-Path $WorkDir "runtime/loopforge_runner.py"

Invoke-Expression "$PythonCmd `"$RunnerPath`" --work-dir `"$WorkDir`" --code-dir `"$CodeDir`" --init --self-check --detect"
