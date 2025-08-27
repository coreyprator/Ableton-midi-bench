param(
    [string]$Instance    = "(localdb)\MSSQLLocalDB",   # Change to ".\SQLEXPRESS" if desired
    [string]$Database    = "ableton-midi-bench",
    [string]$BackupDir   = "$PSScriptRoot\..\backups",
    [int]   $Keep        = 10,                         # keep last N backups; set 0 to disable pruning
    [switch]$Verify                                      # if set, run RESTORE VERIFYONLY after backup
)

$ErrorActionPreference = "Stop"

function Write-Info($msg)  { Write-Host "[BACKUP] $msg" -ForegroundColor Cyan }
function Write-Warn($msg)  { Write-Host "[WARN]   $msg" -ForegroundColor Yellow }
function Write-Err ($msg)  { Write-Host "[ERROR]  $msg" -ForegroundColor Red }

try {
    # Ensure sqlcmd is available
    $sqlcmd = Get-Command sqlcmd -ErrorAction SilentlyContinue
    if (-not $sqlcmd) {
        throw "sqlcmd not found. Install SQL Server Command Line Utilities or add sqlcmd to PATH."
    }

    # Ensure backup directory exists
    $BackupDir = (Resolve-Path -LiteralPath (New-Item -ItemType Directory -Force -Path $BackupDir)).Path
    $timestamp = Get-Date -Format 'yyyyMMdd_HHmmss'
    $bakName   = "{0}_{1}.bak" -f ($Database -replace '[^\w\-]+','_'), $timestamp
    $bakPath   = Join-Path $BackupDir $bakName

    Write-Info "Instance: $Instance"
    Write-Info "Database: $Database"
    Write-Info "Output  : $bakPath"

    # Build and run the T-SQL from backup.sql
    $backupSql = Get-Content -Raw -LiteralPath "$PSScriptRoot\backup.sql"
    # Replace tokens
    $backupSql = $backupSql.Replace("{{DB_NAME}}", $Database).Replace("{{BAK_PATH}}", $bakPath)

    # Run BACKUP DATABASE
    Write-Info "Executing BACKUP DATABASE via sqlcmd..."
    & $sqlcmd.Path -S $Instance -E -b -Q $backupSql

    if ($LASTEXITCODE -ne 0) {
        throw "sqlcmd returned exit code $LASTEXITCODE"
    }

    Write-Info "Backup complete."

    if ($Verify) {
        Write-Info "Verifying backup..."
        $verifySql = "RESTORE VERIFYONLY FROM DISK = N'$bakPath';"
        & $sqlcmd.Path -S $Instance -E -b -Q $verifySql
        if ($LASTEXITCODE -ne 0) {
            throw "RESTORE VERIFYONLY failed (exit code $LASTEXITCODE)."
        }
        Write-Info "Verify succeeded."
    }

    if ($Keep -gt 0) {
        Write-Info "Pruning to keep last $Keep backups..."
        $files = Get-ChildItem -LiteralPath $BackupDir -Filter "*.bak" | Sort-Object LastWriteTime -Descending
        $toDelete = $files | Select-Object -Skip $Keep
        foreach ($f in $toDelete) {
            Write-Info "Deleting old backup: $($f.FullName)"
            Remove-Item -LiteralPath $f.FullName -Force
        }
    }

    Write-Info "Done."
    exit 0
}
catch {
    Write-Err $_
    exit 1
}
