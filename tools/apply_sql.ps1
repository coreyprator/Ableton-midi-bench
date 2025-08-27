param(
    [string]$Instance = "(localdb)\MSSQLLocalDB",
    [string]$Database = "ableton-midi-bench"
)

$ErrorActionPreference = 'Stop'
$sqlcmd = Get-Command sqlcmd -ErrorAction SilentlyContinue
if (-not $sqlcmd) {
    throw "sqlcmd not found. Install SQL Server Command Line Utilities or add sqlcmd to PATH."
}

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
