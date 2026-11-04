# BalapinBridge build (Windows PowerShell)
# 1. Build EXE onefile:  .\build_exe.ps1
# 2. Setup di PC target (Admin):  .\dist\BalapinBridge.exe --setup

$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot

if (-not (Test-Path .\.venv\Scripts\Activate.ps1)) {
  py -m venv .venv
}
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

pyinstaller BalapinBridge.spec

Write-Host ''
Write-Host 'OK -> dist\BalapinBridge.exe'
Write-Host 'Lanjut (Run as Administrator): dist\BalapinBridge.exe --setup'
Write-Host 'Desktop harian: klik EXE (running->info, ready->start, hilang->manual)'
