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
$ValidSource = Join-Path $TempRoot "valid-source"

New-Item -ItemType Directory -Force -Path $NegativeSource | Out-Null
New-Item -ItemType Directory -Force -Path $PositiveSource | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $ValidSource "src") | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $ValidSource "tests") | Out-Null
Set-Content -Path (Join-Path $PositiveSource "README.md") -Value @"
# Positive Smoke Source

Output project: demo_rust
"@
Set-Content -Path (Join-Path $ValidSource "README.md") -Value @"
# Valid Fallback Source

Project Name: Demo C Library
Output project: demo_rust
Source directories: src
Test directories: tests
"@
Set-Content -Path (Join-Path $ValidSource "src\demo.h") -Value @"
void demo_init(void);
int demo_count(void);
"@
Set-Content -Path (Join-Path $ValidSource "src\demo.c") -Value @"
void demo_init(void) {}
int demo_count(void) { return 0; }
"@
Set-Content -Path (Join-Path $ValidSource "tests\test_demo.c") -Value @"
void test_demo_count(void) {
    demo_init();
    demo_count();
}
"@

function Invoke-RunCase {
    param(
        [string]$SourceRoot,
        [string]$ExpectedStatus,
        [string[]]$ExpectedIssueCodes
    )

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
    if (-not $OutputText.Contains("status: ``$ExpectedStatus``")) {
        throw "smoke test failed: expected status $ExpectedStatus"
    }
    foreach ($IssueCode in $ExpectedIssueCodes) {
        if (-not $IssueText.Contains($IssueCode)) {
            throw "smoke test failed: expected issue code $IssueCode"
        }
    }
}

try {
    Invoke-RunCase -SourceRoot $NegativeSource -ExpectedStatus "BLOCKED_WITH_REPORT" -ExpectedIssueCodes @("readme_missing", "source_layout_missing")
    Invoke-RunCase -SourceRoot $PositiveSource -ExpectedStatus "BLOCKED_WITH_REPORT" -ExpectedIssueCodes @("source_layout_missing")
    Invoke-RunCase -SourceRoot $ValidSource -ExpectedStatus "READY_FOR_EVALUATION" -ExpectedIssueCodes @("no_blocking_issues")

    Write-Output "smoke test passed"
}
finally {
    if (Test-Path $TempRoot) {
        Remove-Item -Recurse -Force $TempRoot
    }
}
