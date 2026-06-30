param()

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

$RootDir = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$WorkDir = Join-Path $RootDir "work"
$ResultDir = Join-Path $RootDir "result"
$LogDir = Join-Path $RootDir "logs"
$PythonCmd = Resolve-Python
$RunnerPath = Join-Path $WorkDir "runtime/loopforge_runner.py"

$TempRoot = Join-Path ([System.IO.Path]::GetTempPath()) ("loopforge-smoke-" + [System.Guid]::NewGuid().ToString("N"))
$NegativeSource = Join-Path $TempRoot "no-readme-source"
$PositiveSource = Join-Path $TempRoot "with-readme-source"

New-Item -ItemType Directory -Force -Path $NegativeSource | Out-Null
New-Item -ItemType Directory -Force -Path $PositiveSource | Out-Null
Set-Content -Path (Join-Path $PositiveSource "README.md") -Value @"
# Positive Smoke Source

Task: verify the runner can discover a README from SOURCE_ROOT.
Constraint: no manual config editing is allowed.
"@

function Invoke-RunCase {
    param(
        [string]$SourceRoot,
        [string]$ExpectedReadme,
        [string]$ExpectedIssueText
    )

    $ArtifactDir = Join-Path $SourceRoot ".loopforge"
    if (Test-Path $ArtifactDir) {
        Remove-Item -Recurse -Force $ArtifactDir
    }

    $OutputPath = Join-Path $ResultDir "output.md"
    $IssuePath = Join-Path $ResultDir "issues/00-summary.md"
    $TracePath = Join-Path $LogDir "trace/run-summary.json"

    Remove-Item -Force $OutputPath -ErrorAction SilentlyContinue
    Remove-Item -Force $IssuePath -ErrorAction SilentlyContinue
    Remove-Item -Force $TracePath -ErrorAction SilentlyContinue

    Invoke-Expression "$PythonCmd `"$RunnerPath`" --work-dir `"$WorkDir`" --source-root `"$SourceRoot`" --result-dir `"$ResultDir`" --log-dir `"$LogDir`" --run"

    foreach ($path in @($OutputPath, $IssuePath, $TracePath)) {
        if (-not (Test-Path $path)) {
            throw "smoke test failed: missing required artifact: $path"
        }
    }

    $OutputText = Get-Content -Raw $OutputPath
    $IssueText = Get-Content -Raw $IssuePath
    $ExpectedReadmeLine = "selected_source_readme: ``$ExpectedReadme``"
    if (-not $OutputText.Contains($ExpectedReadmeLine)) {
        throw "smoke test failed: expected selected_source_readme $ExpectedReadme"
    }
    if (-not $IssueText.Contains($ExpectedIssueText)) {
        throw "smoke test failed: expected issue text $ExpectedIssueText"
    }
}

try {
    Invoke-RunCase -SourceRoot $NegativeSource -ExpectedReadme "missing" -ExpectedIssueText "source README not found"
    Invoke-RunCase -SourceRoot $PositiveSource -ExpectedReadme (Join-Path $PositiveSource "README.md") -ExpectedIssueText "no runnable verification commands were derived from source README or framework defaults"

    $TraceText = Get-Content -Raw (Join-Path $LogDir "trace/run-summary.json")
    if ($TraceText -notmatch '"found": true') {
        throw "smoke test failed: positive trace does not record source_readme found=true"
    }
    if ($TraceText -notmatch 'README.md') {
        throw "smoke test failed: positive trace does not record README path"
    }

    Write-Output "smoke test passed"
}
finally {
    if (Test-Path $TempRoot) {
        Remove-Item -Recurse -Force $TempRoot
    }
}
