param(
    [string]$Instance = "",
    [string]$Database = ""
)

$ErrorActionPreference = 'Stop'
$sqlcmd = Get-Command sqlcmd -ErrorAction SilentlyContinue
if (-not $sqlcmd) {
    throw "sqlcmd not found. Install SQL Server Command Line Utilities or add sqlcmd to PATH."
}

# Prefer environment variables if parameters not supplied
if (-not $Instance -and $env:MIDI_BENCH_SQL_SERVER) { $Instance = $env:MIDI_BENCH_SQL_SERVER }
if (-not $Database -and $env:MIDI_BENCH_SQL_DATABASE) { $Database = $env:MIDI_BENCH_SQL_DATABASE }
if (-not $Instance) { throw "No SQL Instance specified. Provide -Instance or set MIDI_BENCH_SQL_SERVER." }
if (-not $Database) { throw "No Database specified. Provide -Database or set MIDI_BENCH_SQL_DATABASE." }

$SqlDir = Join-Path $PSScriptRoot 'sql'
$SqlFiles = Get-ChildItem -Path $SqlDir -Filter *.sql | Sort-Object Name
foreach ($file in $SqlFiles) {
    Write-Host "[APPLY_SQL] Applying $($file.Name) ..."
    & $sqlcmd.Path -S $Instance -d $Database -E -b -i $file.FullName
    if ($LASTEXITCODE -ne 0) {
        throw "sqlcmd failed on $($file.Name) (exit code $LASTEXITCODE)"
    }
}
Write-Host "[APPLY_SQL] All migrations applied."
