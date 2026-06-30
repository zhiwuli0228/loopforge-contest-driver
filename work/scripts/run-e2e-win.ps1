param(
    [string]$SourceRoot = ""
)

$ErrorActionPreference = "Stop"

$RootDir = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$WorkDir = Join-Path $RootDir "work"
$ResultDir = Join-Path $RootDir "result"
$LogDir = Join-Path $RootDir "logs"
$ExperimentDir = Join-Path $LogDir "trace\experiments\run-e2e-win-001"
$ReadmeCandidates = @("README.md", "README", "READNE.md", "readme.md", "Readme.md")

function Write-ExperimentLine {
    param([string]$Message)
    Write-Host "[LoopForge] $Message"
}

function Test-SourceRootLike {
    param([Parameter(Mandatory = $true)][string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) {
        return $false
    }
    foreach ($candidate in $ReadmeCandidates) {
        if (Test-Path -LiteralPath (Join-Path $Path $candidate)) {
            return $true
        }
    }
    if ((Test-Path -LiteralPath (Join-Path $Path "src")) -and (Test-Path -LiteralPath (Join-Path $Path "tests"))) {
        return $true
    }
    return $false
}

function Resolve-SourceRootCandidate {
    param([string]$RequestedSourceRoot)

    if ($RequestedSourceRoot -and $RequestedSourceRoot.Trim() -ne "") {
        $candidate = $RequestedSourceRoot.Trim()
        if (-not (Test-Path -LiteralPath $candidate)) {
            return $null
        }
        $resolved = (Resolve-Path -LiteralPath $candidate).Path
        if ($resolved -match '(?i)\\work\\code$|/work/code$') {
            return $null
        }
        if (Test-SourceRootLike -Path $resolved) {
            return $resolved
        }
        return $null
    }

    return $null
}

function Resolve-SourceRootFromCode {
    $codeRoot = Join-Path $RootDir "code"
    if (-not (Test-Path -LiteralPath $codeRoot)) {
        return $null
    }
    $children = @(Get-ChildItem -LiteralPath $codeRoot -Directory -ErrorAction SilentlyContinue)
    $validChildren = @()
    foreach ($child in $children) {
        if (Test-SourceRootLike -Path $child.FullName) {
            $validChildren += $child.FullName
        }
    }
    if ($validChildren.Count -eq 1) {
        return (Resolve-Path -LiteralPath $validChildren[0]).Path
    }
    if ($validChildren.Count -eq 0 -and (Test-SourceRootLike -Path $codeRoot)) {
        return (Resolve-Path -LiteralPath $codeRoot).Path
    }
    return $null
}

function Write-Diagnosis {
    param(
        [Parameter(Mandatory = $true)][string]$Status,
        [Parameter(Mandatory = $true)][string]$FirstBlockingPoint,
        [string]$DerivedOutputProject = ""
    )

    $lines = @(
        "# Diagnosis",
        "",
        "status: $Status",
        "first_blocking_point: $FirstBlockingPoint"
    )
    if ($DerivedOutputProject -and $DerivedOutputProject.Trim() -ne "") {
        $lines += "derived_output_project: $DerivedOutputProject"
    }
    Set-Content -LiteralPath (Join-Path $ExperimentDir "diagnosis.md") -Value ($lines -join "`r`n") -Encoding UTF8
}

function Read-TextIfExists {
    param([string]$Path)
    if (Test-Path -LiteralPath $Path) {
        return Get-Content -LiteralPath $Path -Raw
    }
    return ""
}

New-Item -ItemType Directory -Force -Path (Join-Path $LogDir "trace") | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $LogDir "trace\experiments") | Out-Null
New-Item -ItemType Directory -Force -Path $ExperimentDir | Out-Null
Remove-Item -LiteralPath (Join-Path $LogDir "trace\experiments\run-e2e-win-001") -Recurse -Force -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force -Path $ExperimentDir | Out-Null
Remove-Item -LiteralPath (Join-Path $LogDir "trace\c-to-rust") -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -LiteralPath (Join-Path $ExperimentDir "diagnosis.md") -Force -ErrorAction SilentlyContinue

$interactionPath = Join-Path $LogDir "interaction.md"
if (-not (Test-Path -LiteralPath $interactionPath)) {
    Set-Content -LiteralPath $interactionPath -Value "# Interaction Log`r`n`r`nNo manual interaction.`r`n" -Encoding UTF8
}

$resolvedSourceRoot = Resolve-SourceRootCandidate -RequestedSourceRoot $SourceRoot
if (-not $resolvedSourceRoot) {
    if ($env:SOURCE_ROOT -and $env:SOURCE_ROOT.Trim() -ne "") {
        $resolvedSourceRoot = Resolve-SourceRootCandidate -RequestedSourceRoot $env:SOURCE_ROOT.Trim()
    }
}
if (-not $resolvedSourceRoot) {
    $resolvedSourceRoot = Resolve-SourceRootFromCode
}
if (-not $resolvedSourceRoot) {
    Write-Diagnosis -Status "BLOCKED_WITH_REPORT" -FirstBlockingPoint "A_SOURCE_ROOT"
    Write-ExperimentLine "Unable to resolve a valid SOURCE_ROOT."
    exit 1
}

$pythonVersionLine = if (Get-Command python -ErrorAction SilentlyContinue) {
    (& python --version 2>&1 | Out-String).TrimEnd()
} elseif (Get-Command py -ErrorAction SilentlyContinue) {
    (& py -3 --version 2>&1 | Out-String).TrimEnd()
} else {
    "Python is not available."
}

$environmentLines = @(
    "# Environment",
    "",
    "## PSVersionTable",
    "",
    (($PSVersionTable | Out-String).TrimEnd()),
    "",
    "## cmd /c ver",
    "",
    ((cmd /c ver) -join "`r`n"),
    "",
    "## python --version / py -3 --version",
    "",
    $pythonVersionLine,
    "",
    "## cargo --version",
    "",
    ((& cargo --version) -join "`r`n"),
    "",
    "## rustc --version",
    "",
    ((& rustc --version) -join "`r`n"),
    "",
    "## git rev-parse HEAD",
    "",
    ((& git rev-parse HEAD) -join "`r`n"),
    ""
)
Set-Content -LiteralPath (Join-Path $ExperimentDir "environment.md") -Value ($environmentLines -join "`r`n") -Encoding UTF8

$pythonCmd = if (Get-Command python -ErrorAction SilentlyContinue) { "python" } elseif (Get-Command py -ErrorAction SilentlyContinue) { "py" } else { $null }
if (-not $pythonCmd) {
    Write-Diagnosis -Status "BLOCKED_WITH_REPORT" -FirstBlockingPoint "G_REPORT_OR_LAUNCHER"
    Write-ExperimentLine "Python is not available."
    exit 1
}

$harnessStdout = ""
$harnessStderr = ""
Write-ExperimentLine "SOURCE_ROOT=$resolvedSourceRoot"
& $pythonCmd (Join-Path $WorkDir "runtime\loopforge_runner.py") --work-dir work --result-dir result --log-dir logs --source-root $resolvedSourceRoot --run 1> (Join-Path $ExperimentDir "harness.stdout.log") 2> (Join-Path $ExperimentDir "harness.stderr.log")
if ($LASTEXITCODE -ne 0) {
    $harnessStdout = Read-TextIfExists -Path (Join-Path $ExperimentDir "harness.stdout.log")
    $harnessStderr = Read-TextIfExists -Path (Join-Path $ExperimentDir "harness.stderr.log")
    if (($harnessStdout -match 'invalid_source_root') -or ($harnessStdout -match 'selected_source_readme:\s*`?work/code/README\.md`?') -or ($harnessStdout -match 'source_root:\s*`?work/code`?') -or ($harnessStderr -match 'invalid_source_root')) {
        Write-Diagnosis -Status "BLOCKED_WITH_REPORT" -FirstBlockingPoint "A_SOURCE_ROOT"
    } else {
        Write-Diagnosis -Status "BLOCKED_WITH_REPORT" -FirstBlockingPoint "G_REPORT_OR_LAUNCHER"
    }
    exit $LASTEXITCODE
}

Copy-Item -LiteralPath (Join-Path $ResultDir "output.md") -Destination (Join-Path $ExperimentDir "output.md") -Force -ErrorAction SilentlyContinue
Copy-Item -LiteralPath (Join-Path $ResultDir "issues\00-summary.md") -Destination (Join-Path $ExperimentDir "issues.md") -Force -ErrorAction SilentlyContinue
Copy-Item -LiteralPath (Join-Path $LogDir "trace\c-to-rust\01-source-inventory.json") -Destination (Join-Path $ExperimentDir "source-inventory.json") -Force -ErrorAction SilentlyContinue
Copy-Item -LiteralPath (Join-Path $LogDir "trace\c-to-rust\02-api-mapping.json") -Destination (Join-Path $ExperimentDir "api-mapping.json") -Force -ErrorAction SilentlyContinue
Copy-Item -LiteralPath (Join-Path $LogDir "trace\c-to-rust\04-test-mapping.json") -Destination (Join-Path $ExperimentDir "test-mapping.json") -Force -ErrorAction SilentlyContinue
Copy-Item -LiteralPath (Join-Path $LogDir "trace\c-to-rust\06-verification-report.md") -Destination (Join-Path $ExperimentDir "verification-report.md") -Force -ErrorAction SilentlyContinue
Copy-Item -LiteralPath (Join-Path $LogDir "trace\c-to-rust\unsafe-ratio.json") -Destination (Join-Path $ExperimentDir "unsafe-ratio.json") -Force -ErrorAction SilentlyContinue

$resultOutput = Read-TextIfExists -Path (Join-Path $ResultDir "output.md")
$derivedOutputProject = $null
if ($resultOutput -match '(?m)^\s*-\s*rust_project:\s*`([^`]+)`\s*$') {
    $derivedOutputProject = $Matches[1]
} elseif ($resultOutput -match '(?m)^\s*derived_output_project:\s*`([^`]+)`\s*$') {
    $derivedOutputProject = $Matches[1]
} else {
    $runSummary = Read-TextIfExists -Path (Join-Path $LogDir "trace\c-to-rust\run-summary.json")
    if ($runSummary -match '"output_project_dir"\s*:\s*"([^"]+)"') {
        $derivedOutputProject = $Matches[1]
    }
}

if (-not $derivedOutputProject) {
    if (($resultOutput -match 'invalid_source_root') -or (($resultOutput + $harnessStdout + $harnessStderr) -match 'selected_source_readme:\s*`?work/code/README\.md`?') -or (($resultOutput + $harnessStdout + $harnessStderr) -match 'source_root:\s*`?work/code`?')) {
        Write-Diagnosis -Status "BLOCKED_WITH_REPORT" -FirstBlockingPoint "A_SOURCE_ROOT"
    } else {
        Write-Diagnosis -Status "BLOCKED_WITH_REPORT" -FirstBlockingPoint "B_REQUIREMENT_PARSE"
    }
    exit 1
}

$derivedOutputProject = [IO.Path]::GetFullPath((Join-Path $RootDir $derivedOutputProject))
if (-not (Test-Path -LiteralPath (Join-Path $derivedOutputProject "Cargo.toml"))) {
    if (($resultOutput -match 'invalid_source_root') -or (($resultOutput + $harnessStdout + $harnessStderr) -match 'selected_source_readme:\s*`?work/code/README\.md`?') -or (($resultOutput + $harnessStdout + $harnessStderr) -match 'source_root:\s*`?work/code`?')) {
        Write-Diagnosis -Status "BLOCKED_WITH_REPORT" -FirstBlockingPoint "A_SOURCE_ROOT" -DerivedOutputProject $derivedOutputProject
        exit 1
    }
    Write-Diagnosis -Status "BLOCKED_WITH_REPORT" -FirstBlockingPoint "D_RUST_GENERATION" -DerivedOutputProject $derivedOutputProject
    exit 1
}

$generatedFiles = Get-ChildItem -LiteralPath $derivedOutputProject -Recurse -File | ForEach-Object { $_.FullName }
Set-Content -LiteralPath (Join-Path $ExperimentDir "generated-files.txt") -Value ($generatedFiles -join "`r`n") -Encoding UTF8

Push-Location $derivedOutputProject
try {
    & cmd /c "cargo build > `"$($ExperimentDir)\cargo-build.log`" 2>&1"
    if ($LASTEXITCODE -ne 0) {
        Write-Diagnosis -Status "BLOCKED_WITH_REPORT" -FirstBlockingPoint "E_CARGO_BUILD" -DerivedOutputProject $derivedOutputProject
        exit $LASTEXITCODE
    }
    & cmd /c "cargo test > `"$($ExperimentDir)\cargo-test.log`" 2>&1"
    if ($LASTEXITCODE -ne 0) {
        Write-Diagnosis -Status "BLOCKED_WITH_REPORT" -FirstBlockingPoint "F_CARGO_TEST_OR_SEMANTIC" -DerivedOutputProject $derivedOutputProject
        exit $LASTEXITCODE
    }
} finally {
    Pop-Location
}

Set-Content -LiteralPath (Join-Path $ExperimentDir "diagnosis.md") -Value @(
    "# Diagnosis",
    "",
    "status: READY_FOR_EVALUATION",
    "first_blocking_point: none",
    "derived_output_project: $derivedOutputProject"
) -Encoding UTF8
exit 0
