param(
    [string]$WorkDir = "work",
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
$ArtifactDir = Join-Path $CodeDir ".loopforge"
$RunnerPath = Join-Path $WorkDir "runtime/loopforge_runner.py"

powershell -ExecutionPolicy Bypass -File (Join-Path $WorkDir "scripts/bootstrap.ps1") -WorkDir $WorkDir -CodeDir $CodeDir
Invoke-Expression "$PythonCmd `"$RunnerPath`" --work-dir `"$WorkDir`" --code-dir `"$CodeDir`" --snapshot smoke"
Invoke-Expression "$PythonCmd `"$RunnerPath`" --work-dir `"$WorkDir`" --code-dir `"$CodeDir`" --verify"
Invoke-Expression "$PythonCmd `"$RunnerPath`" --work-dir `"$WorkDir`" --code-dir `"$CodeDir`" --finalize"

$requiredPaths = @(
    $ArtifactDir,
    (Join-Path $ArtifactDir "runtime/loopforge_runner.py"),
    (Join-Path $ArtifactDir "state/loop-state.json"),
    (Join-Path $ArtifactDir "state/config-check-summary.json"),
    (Join-Path $ArtifactDir "state/profile-check-summary.json"),
    (Join-Path $ArtifactDir "state/work-package-summary.json"),
    (Join-Path $ArtifactDir "state/verification-summary.json"),
    (Join-Path $ArtifactDir "gates/gate-events.md"),
    (Join-Path $ArtifactDir "plan/mode-artifacts.md"),
    (Join-Path $ArtifactDir "snapshots/smoke.diff"),
    (Join-Path $ArtifactDir "reports/final-report.md")
)

foreach ($path in $requiredPaths) {
    if (-not (Test-Path $path)) {
        throw "smoke test failed: missing required artifact: $path"
    }
}

if (Test-Path (Join-Path $WorkDir ".loopforge")) {
    throw "smoke test failed: runtime artifacts escaped into $WorkDir/.loopforge"
}

$reportPath = Join-Path $ArtifactDir "reports/final-report.md"
$reportText = Get-Content -Raw $reportPath
if ($reportText -notmatch "## Contract Validation") {
    throw "smoke test failed: final report is missing contract validation section"
}
if ($reportText -notmatch "BLOCKED_WITH_REPORT") {
    throw "smoke test failed: final report did not record blocked verification"
}
if ($reportText -notmatch "## Mode Artifact Summary") {
    throw "smoke test failed: final report is missing mode artifact summary section"
}

$modeArtifactPath = Join-Path $ArtifactDir "plan/mode-artifacts.md"
$modeArtifactText = Get-Content -Raw $modeArtifactPath
if ($modeArtifactText -notmatch "# Mode Artifacts") {
    throw "smoke test failed: mode artifact index was not initialized"
}

Write-Output "smoke test passed"
