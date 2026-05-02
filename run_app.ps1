Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Set-Location -Path $PSScriptRoot

Write-Host ""
Write-Host "Humanitarian Market Price Early Warning System"
Write-Host "================================================="
Write-Host ""
Write-Host "1. Install/update dependencies and run app"
Write-Host "2. Run app only"
Write-Host "3. Exit"
Write-Host ""

$choice = Read-Host "Choose an option"

if ($choice -eq "3") {
    exit 0
}

if (-not (Test-Path ".venv\Scripts\python.exe")) {
    Write-Host "Creating virtual environment in .venv ..."
    python -m venv .venv
}

if ($choice -eq "1") {
    Write-Host "Installing or updating dependencies ..."
    .\.venv\Scripts\python.exe -m pip install -r requirements.txt
}
elseif ($choice -ne "2") {
    Write-Host "Unknown option."
    exit 1
}

Write-Host ""
Write-Host "Starting Streamlit at http://localhost:8501"
Write-Host "Press Ctrl+C to stop the app."
Write-Host ""

.\.venv\Scripts\python.exe -m streamlit run app.py
