# One-time setup on Windows: Python env, browser, speech-to-text, Instagram login.
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

function Step($what, [scriptblock]$cmd) {
  Write-Host "`n==> $what" -ForegroundColor Cyan
  & $cmd
  if ($LASTEXITCODE -ne 0) { Write-Host "FAILED: $what (exit $LASTEXITCODE). Copy the error above." -ForegroundColor Red; exit 1 }
}

if (-not (Get-Command ffmpeg -ErrorAction SilentlyContinue)) {
  Step "Installing ffmpeg" { winget install -e --id Gyan.FFmpeg --accept-source-agreements --accept-package-agreements }
  $env:Path += ";$env:LOCALAPPDATA\Microsoft\WinGet\Links"
}
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
  Step "Installing Python" { winget install -e --id Python.Python.3.12 --accept-source-agreements --accept-package-agreements }
  Write-Host "Python installed - close this window, open a new PowerShell here and run .\setup.ps1 again."; exit
}

$py = "$PSScriptRoot\.venv\Scripts\python.exe"
if (-not (Test-Path $py)) { Step "Creating virtual environment" { python -m venv .venv } }
Step "Upgrading pip"                { & $py -m pip install -q --upgrade pip }
Step "Installing instatools"        { & $py -m pip install -q -e ".[transcribe]" }
Step "Downloading browser"          { & $py -m playwright install chromium }

if (-not $env:ANTHROPIC_API_KEY) {
  $key = Read-Host "Anthropic API key (sk-ant-...)"
  setx ANTHROPIC_API_KEY $key | Out-Null; $env:ANTHROPIC_API_KEY = $key
}
$bin = "$PSScriptRoot\.venv\Scripts"
$userPath = [Environment]::GetEnvironmentVariable("Path", "User")
if ($userPath -notlike "*$bin*") { [Environment]::SetEnvironmentVariable("Path", "$userPath;$bin", "User") }

Step "Instagram login (log in in the browser window, then press Enter here)" { & "$bin\instatools.exe" login }
Write-Host "`nDone. Open a NEW PowerShell window and try: instatools whoami" -ForegroundColor Green
