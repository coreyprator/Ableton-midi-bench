<# 
Archive the Ableton-midi-bench project with smart excludes.

- Excludes: .git, virtual envs, site-packages, caches, build/dist, runs/output/tmp/logs,
            compiled binaries (.dll/.pyd/.pyc), cloud pointer files (.gsheet), and large media.
- Produces: archive\YYYYMMDD_HHMMSS_Ableton-midi-bench.zip
- Optional: add whitelist patterns to $IncludePatterns to keep specific subfolders (e.g., kept runs).

Tested on Windows 11 / PowerShell 5+.

Usage: 
 & "G:\My Drive\Code\Python\Ableton-midi-bench\Archive Project.ps1" 
#>

$ErrorActionPreference = 'Stop'

# -------- SETTINGS (edit these to taste) --------
# Project root (default: directory containing this script)
$ProjectRoot = $PSScriptRoot

# Output folder for zips
$ArchiveDir = Join-Path $ProjectRoot 'archive'

# Optional whitelist: any path matching these regex patterns will be INCLUDED
# even if parent directories/extensions are excluded.
# Example: keep a curated set of output runs:
$IncludePatterns = @(
    # 'runs\\kept_runs\\'   # uncomment and adjust if needed
)

# Directory name fragments to exclude (regex OR group is generated)
$DirExcludeNames = @(
    '\.git',
    'archive',
    '\.venv', '^venv$', '^env$',
    'site-packages', 'dist-packages',
    '__pycache__', '\.pytest_cache', '\.mypy_cache', '\.ipynb_checkpoints',
    '\.ruff_cache', '\.cache',
    '^build$', '^dist$',
    '^runs$', '^output$', '^tmp$', '^artifacts$', '^logs$',
    '^node_modules$' # just in case
)

# File extensions to exclude (case-insensitive)
$ExtExcludeList = @(
    '.dll', '.pyd', '.pyc', '.gsheet', '.exe',
    # common large media
    '.wav', '.aiff', '.aif', '.mp3', '.flac',
    '.mp4', '.mov', '.avi', '.mkv',
    # common archives / disk images
    '.zip', '.7z', '.rar', '.iso', '.pak'
)

# -------- SCRIPT START --------
if (-not (Test-Path $ArchiveDir)) { New-Item -Path $ArchiveDir -ItemType Directory | Out-Null }

$timestamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$zipName   = "${timestamp}_Ableton-midi-bench.zip"
$zipPath   = Join-Path $ArchiveDir $zipName

Write-Host "[ARCHIVE] Root: $ProjectRoot"
Write-Host "[ARCHIVE] Out : $zipPath"

# Build a single regex that matches any excluded directory segment
# We want to exclude if the path contains \DirName\ anywhere.
$dirOrGroup = ($DirExcludeNames | ForEach-Object { "($_)" }) -join '|'
$DirExcludeRegex = "\\(?:$dirOrGroup)(?:\\|$)"  # segment boundary

# Normalize extension excludes to lowercase for comparisons
$ExtExcludeHash = @{}
foreach ($ext in $ExtExcludeList) { $ExtExcludeHash[$ext.ToLower()] = $true }

function Test-MatchAny {
    param(
        [string]$Text,
        [string[]]$Patterns
    )
    foreach ($p in $Patterns) {
        if ($Text -match $p) { return $true }
    }
    return $false
}

try {
    # Gather all files under root (excluding the archive dir itself via directory regex)
    $allFiles = Get-ChildItem -Path $ProjectRoot -Recurse -File -Force


    # Compute parent of project root for archiving with folder name
    $ParentDir = Split-Path $ProjectRoot -Parent
    $ProjectFolderName = Split-Path $ProjectRoot -Leaf

    $selected = @()
    foreach ($f in $allFiles) {
        $full = $f.FullName
        # Path relative to parent, so zip contains the project folder
        $relToParent = Resolve-Path -LiteralPath $full | ForEach-Object { $_.Path.Substring($ParentDir.Length).TrimStart('\','/') }
        $relBs = $relToParent -replace '/', '\'

        # 1) Whitelist wins: include if it matches any include pattern
        $isWhitelisted = ($IncludePatterns.Count -gt 0) -and (Test-MatchAny -Text $relBs -Patterns $IncludePatterns)
        if ($isWhitelisted) {
            $selected += [PSCustomObject]@{ FullName = $full; RelPath = $relBs }
            continue
        }

        # 2) Exclude if the relative path contains any excluded directory segment
        if ($relBs -match $DirExcludeRegex) { continue }

        # 3) Exclude by extension
        $ext = [System.IO.Path]::GetExtension($full).ToLower()
        if ($ExtExcludeHash.ContainsKey($ext)) { continue }

        # Otherwise keep it
        $selected += [PSCustomObject]@{ FullName = $full; RelPath = $relBs }
    }


    if (-not $selected -or $selected.Count -eq 0) {
        Write-Warning "[ARCHIVE] No files selected. Check your exclude patterns."
        exit 0
    }

    Write-Host ("[ARCHIVE] Adding {0} files..." -f $selected.Count)

    # Create zip with folder structure preserved (including project folder)
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    $zip = [System.IO.Compression.ZipFile]::Open($zipPath, [System.IO.Compression.ZipArchiveMode]::Create)
    foreach ($item in $selected) {
        $entryName = $item.RelPath.TrimStart('\','/')
        [System.IO.Compression.ZipFileExtensions]::CreateEntryFromFile($zip, $item.FullName, $entryName)
    }
    $zip.Dispose()

    # Report size
    $zipInfo = Get-Item $zipPath
    $mb = [Math]::Round($zipInfo.Length / 1MB, 2)
    Write-Host "[ARCHIVE] Success: $zipPath  ($mb MB)"

} catch {
    Write-Host "[ARCHIVE] ERROR: Archive failed. $($_.Exception.Message)"
    exit 1
}

# -------- NOTES --------
# 1) To keep specific outputs (e.g., a curated run), add a whitelist pattern above:
#    $IncludePatterns = @('runs\\kept_runs\\')
#
# 2) If you discover other heavy folders, add them to $DirExcludeNames.
# 3) If you need to include media or CSVs for a particular case, temporarily comment them out of the exclude lists.
