<#
.\runui.ps1
PowerShell helper to run the project's GUI without remembering the path or venv.

Usage (from project root):
  .\runui.ps1
  .\runui.ps1 -NoActivate    # skip attempting to activate a virtualenv

Behavior:
- Prefer to activate a virtualenv at `.venv` in the repo root.
- If not found, try `C:\venvs\<ProjectName>\.venv` (common developer mirror).
- If no virtualenv is found or activation fails, falls back to `python` on PATH.
- Runs `python -m src.midi_benchmark.midi_bench_gui` from the repo root.
#>
param(
    [switch]$NoActivate,
    [switch]$InstallProfile
)

Set-StrictMode -Version Latest

# Determine the script directory and project name robustly.
# Prefer built-in variables that are set when the file is executed as a script.
try {
    if ($PSCommandPath) {
        $ScriptDir = Split-Path -Parent $PSCommandPath
    } elseif ($PSScriptRoot) {
        $ScriptDir = $PSScriptRoot
    } elseif ($MyInvocation.MyCommand.Definition) {
        $ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
    } else {
        # Fallback to current location (interactive/sourced scenarios)
        $ScriptDir = (Get-Location).ProviderPath
    }
} catch {
    # On any error, fallback to current working directory
    $ScriptDir = (Get-Location).ProviderPath
}

# Call optional project helper to load machine-specific env vars (tools/.env.local)
$helperPath = Join-Path -Path $ScriptDir -ChildPath "tools\activate-project.ps1"
if (Test-Path $helperPath) {
    Write-Host "Sourcing project helper: $helperPath"
    try {
        . $helperPath
        $env:__MIDI_BENCH_HELPER_LOADED = '1'
    } catch {
        Write-Warning "Failed to dot-source project helper: $_"
    }
} else {
    Write-Host "Project helper not found at $helperPath (skipping)."
}

# Ensure $ScriptDir is a plain path string and not something accidentally injected
if (-not [string]::IsNullOrWhiteSpace($ScriptDir)) {
    $ScriptDir = $ScriptDir.Trim()
    # If the value looks like it contains a command (starts with &), fallback to cwd
    if ($ScriptDir -match '^[&|`"\s]') {
        $ScriptDir = (Get-Location).ProviderPath
    }
} else {
    $ScriptDir = (Get-Location).ProviderPath
}

$ProjectName = Split-Path -Leaf $ScriptDir
if (-not $ProjectName -or $ProjectName -eq '') {
    try { $ProjectName = (Get-Location).Path | Split-Path -Leaf } catch { $ProjectName = 'project' }
}

# Candidate venv locations (repo .venv first, then the C:\venvs mirror)
$preferredVenv = Join-Path -Path "C:\venvs" -ChildPath $ProjectName
$venvCandidates = @(
    (Join-Path -Path $ScriptDir -ChildPath '.venv'),
    $preferredVenv
)

$activatePath = $null
foreach ($v in $venvCandidates) {
    $act = Join-Path -Path $v -ChildPath 'Scripts\Activate.ps1'
    if (Test-Path $act) { $activatePath = $act; break }
}

if (-not $NoActivate) {
    if ($activatePath) {
        Write-Host "Activating virtualenv: $activatePath"
        try {
            # Dot-source so the activation modifies this shell/session
            . $activatePath
        } catch {
            Write-Warning "Failed to activate venv (dot-sourcing). Continuing without activation. Error: $_"
        }
    } else {
        Write-Host "No virtualenv found at .venv or $preferredVenv — using system python if available."
    }
}


# Choose python executable: prefer the activated venv, then known candidates, then 'python' on PATH
$pythonExe = $null
if ($env:VIRTUAL_ENV) {
    $pythonExe = Join-Path $env:VIRTUAL_ENV "Scripts\python.exe"
}
if (-not $pythonExe) {
    foreach ($v in $venvCandidates) {
        $py = Join-Path -Path $v -ChildPath 'Scripts\python.exe'
        if (Test-Path $py) { $pythonExe = $py; break }
    }
}
if (-not $pythonExe) { $pythonExe = "python" }

Write-Host "Using Python: $pythonExe"

Push-Location $ScriptDir
try {
    & $pythonExe -m src.midi_benchmark.midi_bench_gui @args
} finally {
    Pop-Location
}

# Helpful one-liner you can add to your PowerShell profile ($PROFILE) to auto-discover
# this repo under common roots and forward arguments to the repo's runui.ps1.
$oneLiner = @'
function runui {
    param($r='Ableton-midi-bench')
    $roots = @(
        "$env:USERPROFILE\My Drive\Code\Python",
        "$env:USERPROFILE\Documents"
    )
    foreach ($root in $roots) {
        if (Test-Path $root) {
            $p = Get-ChildItem $root -Directory -Recurse -ErrorAction SilentlyContinue |
                Where-Object Name -eq $r | Select-Object -First 1
            if ($p) {
                & (Join-Path $p.FullName 'runui.ps1') @args
                return
            }
        }
    }
    Write-Error "Repo $r not found under common roots."
}
'@

Write-Host "`nTip: to run 'runui' from any PowerShell session without typing .\ add this one-liner to your PowerShell profile ($PROFILE):`n"
Write-Host $oneLiner -ForegroundColor Yellow

if ($InstallProfile) {
    try {
        if (-not (Test-Path $PROFILE)) {
            New-Item -ItemType File -Path $PROFILE -Force | Out-Null
        }
        $resp = Read-Host "Append runui function to your PowerShell profile at $PROFILE? (Y/N)"
        if ($resp -match '^[Yy]') {
            Add-Content -Path $PROFILE -Value "`n$oneLiner`n"
            Write-Host "Appended runui function to $PROFILE" -ForegroundColor Green
        } else {
            Write-Host "Cancelled profile installation." -ForegroundColor Yellow
        }
    } catch {
        Write-Error "Failed to update profile: $_"
    }
}

