<##
# tools/activate-project.ps1
# Helper to set project-specific environment variables for the current PowerShell session.
# Usage (after activating the repo venv):
#   . .\tools\activate-project.ps1
# Optionally pass parameters:
#   . .\tools\activate-project.ps1 -Server '.\SQLEXPRESS01' -Database 'ableton-midi-bench'
##>

param(
    [string]$Server = $null,
    [string]$Database = $null,
    [string]$OdbcDriver = $null,
    [string]$TrustCert = $null,
    [string]$Encrypt = $null
)

function _Load-EnvFile($path) {
    if (-not (Test-Path $path)) { return }
    Get-Content $path | ForEach-Object {
        $line = $_.Trim()
        if (-not $line -or $line.StartsWith('#')) { return }
        $parts = $line -split '=', 2
        if ($parts.Count -ne 2) { return }
        $k = $parts[0].Trim()
        $v = $parts[1].Trim().Trim('"')
        # only set script-level variables (used below) if not explicitly passed
        if (-not (Get-Variable -Name $k -Scope Script -ErrorAction SilentlyContinue)) {
            Set-Variable -Name $k -Value $v -Scope Script
        }
    }
}

try {
    $scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Definition
    $envFile = Join-Path $scriptRoot '.env.local'

    # Load .env.local if present (user-managed, gitignored)
    _Load-EnvFile $envFile

    # Resolve values: prefer explicit parameters -> .env.local -> existing environment
    $sv = Get-Variable -Name 'MIDI_BENCH_SQL_SERVER' -Scope Script -ErrorAction SilentlyContinue
    if ($Server) { $server = $Server }
    elseif ($sv -and $sv.Value) { $server = $sv.Value }
    elseif ($env:MIDI_BENCH_SQL_SERVER) { $server = $env:MIDI_BENCH_SQL_SERVER } else { $server = $null }

    $dv = Get-Variable -Name 'MIDI_BENCH_SQL_DATABASE' -Scope Script -ErrorAction SilentlyContinue
    if ($Database) { $database = $Database }
    elseif ($dv -and $dv.Value) { $database = $dv.Value }
    elseif ($env:MIDI_BENCH_SQL_DATABASE) { $database = $env:MIDI_BENCH_SQL_DATABASE } else { $database = $null }

    $ov = Get-Variable -Name 'MIDI_BENCH_ODBC_DRIVER' -Scope Script -ErrorAction SilentlyContinue
    if ($OdbcDriver) { $odbc = $OdbcDriver }
    elseif ($ov -and $ov.Value) { $odbc = $ov.Value }
    elseif ($env:MIDI_BENCH_ODBC_DRIVER) { $odbc = $env:MIDI_BENCH_ODBC_DRIVER } else { $odbc = $null }

    $tv = Get-Variable -Name 'MIDI_BENCH_TRUST_CERT' -Scope Script -ErrorAction SilentlyContinue
    if ($TrustCert) { $trust = $TrustCert }
    elseif ($tv -and $tv.Value) { $trust = $tv.Value }
    elseif ($env:MIDI_BENCH_TRUST_CERT) { $trust = $env:MIDI_BENCH_TRUST_CERT } else { $trust = $null }

    $ev = Get-Variable -Name 'MIDI_BENCH_ENCRYPT' -Scope Script -ErrorAction SilentlyContinue
    if ($Encrypt) { $encrypt = $Encrypt }
    elseif ($ev -and $ev.Value) { $encrypt = $ev.Value }
    elseif ($env:MIDI_BENCH_ENCRYPT) { $encrypt = $env:MIDI_BENCH_ENCRYPT } else { $encrypt = $null }

    if ($null -ne $server) { $env:MIDI_BENCH_SQL_SERVER = $server }
    if ($null -ne $database) { $env:MIDI_BENCH_SQL_DATABASE = $database }
    if ($null -ne $odbc) { $env:MIDI_BENCH_ODBC_DRIVER = $odbc }
    if ($null -ne $trust) { $env:MIDI_BENCH_TRUST_CERT = $trust }
    if ($null -ne $encrypt) { $env:MIDI_BENCH_ENCRYPT = $encrypt }

    Write-Host "Project environment loaded:" -ForegroundColor Green
    Write-Host "  MIDI_BENCH_SQL_SERVER = $($env:MIDI_BENCH_SQL_SERVER)"
    Write-Host "  MIDI_BENCH_SQL_DATABASE = $($env:MIDI_BENCH_SQL_DATABASE)"
    if ($env:MIDI_BENCH_ODBC_DRIVER) { Write-Host "  MIDI_BENCH_ODBC_DRIVER = $($env:MIDI_BENCH_ODBC_DRIVER)" }
    if ($env:MIDI_BENCH_TRUST_CERT) { Write-Host "  MIDI_BENCH_TRUST_CERT = $($env:MIDI_BENCH_TRUST_CERT)" }
    if ($env:MIDI_BENCH_ENCRYPT) { Write-Host "  MIDI_BENCH_ENCRYPT = $($env:MIDI_BENCH_ENCRYPT)" }

    return 0
}
catch {
    Write-Error "Failed to load project env: $_"
    return 1
}
