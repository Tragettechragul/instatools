# One-time setup on Windows: Python env, browser, speech-to-text, Instagram login.
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
if (-not (Get-Command ffmpeg -ErrorAction SilentlyContinue)) { winget install -e --id Gyan.FFmpeg; $env:Path += ";$env:LOCALAPPDATA\Microsoft\WinGet\Links" }
if (-not (Get-Command python -ErrorAction SilentlyContinue)) { winget install -e --id Python.Python.3.12; Write-Host "Python installed - close and re-run this script."; exit }
python -m venv .venv
.\.venv\Scripts\pip install -q --upgrade pip
.\.venv\Scripts\pip install -q -e ".[transcribe]"
.\.venv\Scripts\playwright install chromium
if (-not $env:ANTHROPIC_API_KEY) {
  $key = Read-Host "Anthropic API key (sk-ant-...)"
  setx ANTHROPIC_API_KEY $key | Out-Null; $env:ANTHROPIC_API_KEY = $key
}
$bin = "$PSScriptRoot\.venv\Scripts"
$userPath = [Environment]::GetEnvironmentVariable("Path", "User")
if ($userPath -notlike "*$bin*") { [Environment]::SetEnvironmentVariable("Path", "$userPath;$bin", "User") }
& "$bin\instatools.exe" login
Write-Host "Done. Open a new terminal and try: instatools analyze <instagram link>"
