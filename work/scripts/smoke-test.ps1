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
$ResultDir = Join-Path $WorkDir "result"
$LogDir = Join-Path $WorkDir "logs"
$PythonCmd = Resolve-Python
$RunnerPath = Join-Path $WorkDir "runtime/loopforge_runner.py"

$TempRoot = Join-Path ([System.IO.Path]::GetTempPath()) ("loopforge-smoke-" + [System.Guid]::NewGuid().ToString("N"))
$NegativeSource = Join-Path $TempRoot "empty-source"
$PositiveSource = Join-Path $TempRoot "source-without-layout"
$ValidSource = Join-Path $TempRoot "valid-source"

New-Item -ItemType Directory -Force -Path $NegativeSource | Out-Null
New-Item -ItemType Directory -Force -Path $PositiveSource | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $ValidSource "src") | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $ValidSource "tests") | Out-Null
Set-Content -Path (Join-Path $ValidSource "src\demo.h") -Value @"
void demo_init(void);
int demo_count(void);
"@
Set-Content -Path (Join-Path $ValidSource "src\demo.c") -Value @"
void demo_init(void) {}
int demo_count(void) { return 0; }
"@
Set-Content -Path (Join-Path $ValidSource "tests\test_demo.c") -Value @"
#include <assert.h>
void test_demo_count(void) {
    demo_init();
    assert(demo_count() == 0);
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

function Invoke-DetectCase {
    param([string]$SourceRoot)
    $DetectPath = Join-Path $LogDir "trace/execution-adapter/state/detect-summary.json"
    Remove-Item -Force $DetectPath -ErrorAction SilentlyContinue
    Invoke-Expression "$PythonCmd `"$RunnerPath`" --work-dir `"$WorkDir`" --source-root `"$SourceRoot`" --result-dir `"$ResultDir`" --log-dir `"$LogDir`" --detect"
    if (-not (Test-Path $DetectPath)) { throw "smoke test failed: missing detect summary" }
    $payload = Get-Content -Raw $DetectPath | ConvertFrom-Json
    if (-not $payload.ok) { throw "smoke test failed: README-free source discovery did not succeed" }
    if ($payload.packet.design_readme_sha256.Length -ne 64) { throw "smoke test failed: design digest missing" }
}

try {
    Invoke-RunCase -SourceRoot $NegativeSource -ExpectedStatus "BLOCKED_WITH_REPORT" -ExpectedIssueCodes @("source_layout_missing")
    Invoke-RunCase -SourceRoot $PositiveSource -ExpectedStatus "BLOCKED_WITH_REPORT" -ExpectedIssueCodes @("source_layout_missing")
    Invoke-DetectCase -SourceRoot $ValidSource

    Write-Output "smoke test passed"
}
finally {
    if (Test-Path $TempRoot) {
        Remove-Item -Recurse -Force $TempRoot
    }
}
