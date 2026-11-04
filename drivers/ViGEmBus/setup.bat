@echo off
REM Balapin V0.3 - install ViGEmBus dari artefak lokal (jalankan sebagai Administrator)
setlocal
set EXE=%~dp0ViGEmBus_1.22.0_x64_x86_arm64.exe
if not exist "%EXE%" (
  echo [ERR] Tidak ketemu: %EXE%
  exit /b 1
)
echo [Balapin] Menginstall ViGEmBus 1.22.0 ...
"%EXE%"
echo [Balapin] Selesai. Cek Win+R - joy.cpl
