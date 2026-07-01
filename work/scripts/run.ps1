param(
    [string]$SourceRoot = ""
)

$ErrorActionPreference = "Stop"

$RootDir = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$WorkDir = Join-Path $RootDir "work"
$ResultDir = Join-Path $RootDir "result"
$LogDir = Join-Path $RootDir "logs"

function Write-LoopForgeError {
    param([string]$Message)
    Write-Host "[LoopForge] ERROR: $Message"
}

function Test-SourceRootLike {
    param([Parameter(Mandatory = $true)][string]$Path)

    if (-not (Test-Path -LiteralPath $Path)) {
        return $false
    }

    $sourceFile = Get-ChildItem -LiteralPath $Path -Recurse -File -ErrorAction SilentlyContinue |
        Where-Object { $_.Extension -in @('.c', '.cc', '.cpp', '.cxx') -and $_.FullName -notmatch '[\\/](?:\.git|build|dist|target|out)[\\/]' } |
        Select-Object -First 1
    return $null -ne $sourceFile
}

function Resolve-UniqueSourceChild {
    param([Parameter(Mandatory = $true)][string]$BasePath)

    if (-not (Test-Path -LiteralPath $BasePath)) {
        return $null
    }

    $children = @(Get-ChildItem -LiteralPath $BasePath -Directory -ErrorAction SilentlyContinue)
    $validChildren = @()
    foreach ($child in $children) {
        if (Test-SourceRootLike -Path $child.FullName) {
            $validChildren += $child.FullName
        }
    }

    if ($validChildren.Count -eq 1) {
        return (Resolve-Path -LiteralPath $validChildren[0]).Path
    }

    return $null
}

function Resolve-SourceRoot {
    param([string]$ExplicitSourceRoot)

    if ($ExplicitSourceRoot -and $ExplicitSourceRoot.Trim() -ne "") {
        $candidate = $ExplicitSourceRoot.Trim()
        if (-not (Test-Path -LiteralPath $candidate)) {
            Write-LoopForgeError "SOURCE_ROOT not found: $candidate"
            exit 1
        }
        $resolved = (Resolve-Path -LiteralPath $candidate).Path
        return $resolved
    }

    if ($env:SOURCE_ROOT -and $env:SOURCE_ROOT.Trim() -ne "") {
        return (Resolve-SourceRoot -ExplicitSourceRoot $env:SOURCE_ROOT.Trim())
    }

    Write-LoopForgeError "SOURCE_ROOT not provided and no valid source project was resolved."
    exit 1
}

New-Item -ItemType Directory -Force -Path $ResultDir | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $ResultDir "issues") | Out-Null
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $LogDir "trace") | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $LogDir "trace\experiments") | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $LogDir "trace\c-to-rust") | Out-Null

$interactionLogPath = Join-Path $LogDir "interaction.md"
if (-not (Test-Path -LiteralPath $interactionLogPath)) {
    Set-Content -LiteralPath $interactionLogPath -Value "# Interaction Log`r`n`r`nNo manual interaction.`r`n" -Encoding UTF8
}

$ResolvedSourceRoot = Resolve-SourceRoot -ExplicitSourceRoot $SourceRoot
Write-Host "[LoopForge] SOURCE_ROOT=$ResolvedSourceRoot"

$pythonCmd = $null
if (Get-Command python -ErrorAction SilentlyContinue) {
    $pythonCmd = "python"
} elseif (Get-Command py -ErrorAction SilentlyContinue) {
    $pythonCmd = "py"
}

if (-not $pythonCmd) {
    Write-LoopForgeError "Python is not available."
    exit 1
}

$runnerPath = Join-Path $WorkDir "runtime\loopforge_runner.py"
$runnerArgs = @(
    $runnerPath,
    "--work-dir", "work",
    "--result-dir", "result",
    "--log-dir", "logs",
    "--source-root", $ResolvedSourceRoot,
    "--run"
)

& $pythonCmd @runnerArgs
exit $LASTEXITCODE
