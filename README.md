# Balapin PC Bridge (V0.2 + V0.3)

Penerima UDP di PC untuk data controller Android (steering/throttle/brake/ABXY).
Terpisah dari repo Android — dijalankan di dalam venv.

## Setup (Windows, sekali saja)

```bat
cd BalapinPCBridge
py -m venv .venv
\.venv\Scripts\activate
pip install -r requirements.txt
```

## Jalankan monitor

```bat
\.venv\Scripts\activate
python udp_monitor.py --port 5005
```

## Alur tes V0.2

1. HP + PC terhubung ke WiFi yang sama.
2. Izinkan UDP port 5005 di firewall Windows (inbound).
3. Cek IP PC (`ipconfig`), masukkan di kolom PC IP pada aplikasi HP.
4. Tekan Connect di HP, miringkan HP + geser pedal gas/rem.
5. Angka di HP dan monitor PC harus bergerak bersamaan (~60 pkt/s,
   latency WiFi lokal umumnya 2–20ms, loss idealnya 0).

## Format paket

```json
{"steering": 0.65, "throttle": 0.0, "brake": 0.0, "buttons": 5, "race": 3, "seq": 123, "ts": 172...}
```

Bitmask tombol: `A=1`, `B=2`, `X=4`, `Y=8` (contoh `5` = A+X).
Bitmask race control: `DRS=1`, `ERS=2`, `ABS=4`, `TC=8`, `PIT_LIMIT=16`, `PIT_IN=32`.

## V0.3 — Bridge ke F1 2020 (konektor & konverter, tanpa filter)

PC hanya clamp + teruskan. Deadzone/sensitivitas/filter milik client HP.

Prasyarat sekali saja: install `drivers\ViGEmBus\ViGEmBus_1.22.0_x64_x86_arm64.exe`
(atau `drivers\ViGEmBus\setup.bat` sebagai Administrator).

```bat
\.venv\Scripts\activate
python udp_to_gamepad.py --port 5005
python udp_to_gamepad.py --port 5005 --dry-run   # tanpa driver, hanya log
```

Mapping: `steering -1..1` -> LeftStick-X, `throttle 0..1` -> RightTrigger,
`brake 0..1` -> LeftTrigger, dan bitmask `buttons` -> A/B/X/Y.
Race mapping: `DRS` -> DPAD UP, `ERS` -> DPAD DOWN, `ABS` -> LB,
`TC` -> RB, `PIT LIMIT` -> BACK, `PIT IN` -> START. Failsafe: >500ms tanpa paket -> netral.
Cek di `joy.cpl`, lalu binding di F1 2020 sebagai gamepad XInput.

## EXE Desktop (BalapinBridge.exe)

Satu EXE untuk setup + pemakaian harian (build: `.\build_exe.ps1`):

```bat
dist\BalapinBridge.exe --setup    :: Run as Admin: cek driver (skip bila ada,
                                   :: install /qn bila belum), lalu TANYA dulu
                                   :: sebelum pasang auto-start ONLOGON
dist\BalapinBridge.exe --status   :: cek driver + task + log file
```

Klik EXE tanpa argumen (shortcut Desktop):
* task `BalapinBridge` Running -> info "service sudah jalan".
* task terinstal tapi berhenti -> `schtasks /Run` otomatis.
* task tidak terinstal -> jalan manual foreground dari EXE ini.
* Auto-start = Scheduled Task ONLOGON (user-mode, bukan SYSTEM service),
  agar `vgamepad`/`joy.cpl`/F1 2020 satu sesi. Kelola via
  `--install-autostart`, `--start`, `--stop`, `--uninstall-autostart`.

## V0.5 — Siap Publikasi (Update Terakhir)

Syarat sebelum disebar ke publik:

### 1. Install Reproducible
`vgamepad==0.1.0` hanya ada sebagai sdist. Pip modern (setuptools baru) gagal
build dengan error "Preparing metadata (pyproject.toml)". Workaround:

```bat
\.venv\Scripts\pip.exe install wheel
\.venv\Scripts\pip.exe install --no-build-isolation --no-cache-dir vgamepad==0.1.0
```
Jika tetap gagal, salin dari Python system:
```bat
Copy-Item -Recurse "$env:LOCALAPPDATA\Programs\Python\Python39\Lib\site-packages\vgamepad" .\.venv\Lib\site-packages\
```

### 2. Lisensi Redistribusi ViGEmBus 1.22.0
Driver ViGEmBus 1.22.0 (keduanya arsitektur x64/arm64) diliburkan bersama
paket ini. Silakan lihat file `LICENSE` untuk ketentuan penggunaan. Driver
ini gratis untuk digunakan dalam konteks non-commercial / pembelajaran, namun
harus mengikuti protokol redistribution dari ViGEm projek.

### 3. Uji Fresh-VM End-to-End
Langkah uji di VM Windows bersih:

```bat
# 1. Jalankan setup sebagai Admin
dist\BalapinBridge.exe --setup

# 2. Cek di joy.cpl muncul Xbox 360 Gamepad
# 3. Binding di F1 2020 terbaca sebagai controller XInput
# 4. Test kirim paket dari HP via UDP

# 5. Uninstall bersih:
#    - Hapus task scheduled: schtasks /Delete /TN "BalapinBridge" /F
#    - Hapus shortcut desktop
#    - Hapus file EXE dan folder app
```

### 4. Paket Rilis
Setiap rilis diasakan sebagai `BalapinBridge-<versi>.zip` yang berisi:

- `BalapinBridge.exe` (single executable)
- `README.md` (singkat, hanya konfigurasi dasar)
- `SHA256.txt` (checksum SHA-256 dari EXE)
- Catatan SmartScreen/AV (tanpa code signing, pengguna bisa
  "More info" -> "Run anyway" jika diblokir)

### 5. Firewall UDP 5005
Aturan inbound UDP port 5005 harus aktif agar HP bisa mengirim data ke PC.
Saat pertama kali menjalankan `--setup` (sebagai Admin), aturan firewall
akan dibuat otomatis. Jika gagal, buat manual:

```netsh
netsh advfirewall firewall add rule name="Balapin PC Bridge UDP 5005" dir=in action=allow protocol=UDP localport=5005
```

### 6. Disclaimer Keamanan
**PENTING:** Aplikasi ini menggunakan komunikasi UDP polos tanpa autentikasi.
Jika dijalankan di jaringan publik atau WiFi yang terbuka, ada risiko
 perangkat lain menyuntik input yang tidak diinginkan (simulasi tombol/
gerak gamepad). Gunakan hanya di jaringan LAN pribadi yang Anda cerna.
Aplikator tidak bertanggung jawab atas kerusakan atau kecurangan yang
diharapkan akibat penggunaan jaringan tidak terpercaya.

### 7. Versioning
Setiap rilis memiliki versi eksplisit:

- **EXE menampilkan versi**: jalankan `BalapinBridge.exe --version`
- **Tag Git**: setiap rilis ditandai dengan tag `v<versi>` (misal: `v1.0.0`)
- **Versi dalam kode**: definisikan di `bridge_app.py` atau `BalapinBridge.spec`

## Kontributor / Kontak

Dibuat dengan ❤️ untuk komunitas racing simulator.