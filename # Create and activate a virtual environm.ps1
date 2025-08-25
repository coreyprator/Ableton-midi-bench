# Create and activate a virtual environment, and update pip

# Create workspace directory if it doesn't exist
$workspace = "G:\My Drive\Code\Python\ableton-midi-bench"
if (!(Test-Path $workspace)) {
    New-Item -ItemType Directory -Path $workspace | Out-Null
}

Set-Location $workspace

# Create virtual environment
py -3 -m venv .venv

# Activate virtual environment
& .\.venv\Scripts\Activate.ps1

# Upgrade pip
python -m pip install -U pip
