# ViGEmBus 1.22.0 — artefak lokal (V0.3)

Installer resmi di-vendor agar setup reproducible tanpa cari link lagi:

- File: `ViGEmBus_1.22.0_x64_x86_arm64.exe` (6.278.576 bytes)
- Sumber: https://github.com/nefarius/ViGEmBus/releases/tag/v1.22.0
- Direct: https://github.com/nefarius/ViGEmBus/releases/download/v1.22.0/ViGEmBus_1.22.0_x64_x86_arm64.exe
- Berlaku: Windows 10/11 x64/x86/arm64. Repo ViGEmBus sudah diarsip (EOL),
  versi 1.22.0 adalah rilis final ("It's dead, Jim"), driver tidak berubah.

## Install (sekali saja, Run as Administrator)

1. Jalankan `setup.bat`, atau manual klik `ViGEmBus_1.22.0_x64_x86_arm64.exe`.
2. Jika upgrade dari versi lama gagal, jalankan installer 2x (bug upstream).
3. Verifikasi: tekan `Win+R` -> `joy.cpl` -> jalankan `udp_to_gamepad.py`,
   seharusnya muncul `Xbox 360 Controller for Windows`.
4. F1 2020 akan mendeteksinya sebagai gamepad XInput.

Silent install (untuk skrip): `ViGEmBus_1.22.0_x64_x86_arm64.exe /qn`
