# Roadmap BalapinPCBridge

## V0.3 — Bridge ke F1 2020 (selesai, lokal)
- [x] UDP monitor (HP -> PC)
- [x] UDP -> virtual Xbox 360 pad (ViGEm), failsafe netral
- [x] EXE onefile `BalapinBridge.exe` (`--setup`, auto-start ONLOGON, mode desktop)
- [x] Teruji di 1 PC dev (driver OK, `joy.cpl` muncul)

## V0.4 — Multiplayer (belum mulai)
Lebih dari 1 HP sebagai controller, dibedakan dari IP pengirim:

- [ ] **State per IP.** `Latest` + statistik (seq/loss/latency) per alamat
      pengirim, bukan satu global. Failsafe netral per klien (>500ms).
- [ ] **N virtual pad.** Satu `VX360Gamepad` per IP (maks 4 slot XInput).
      Slot ditempati saat IP pertama kali kirim paket.
- [ ] **Slot release.** IP yang timeout lama (>N detik, mis. 10s) melepas
      pad-nya agar slot bisa dipakai IP baru. Hindari slot bocor.
- [ ] **Tampilan per klien.** Monitor/EXE log menampilkan tiap IP +
      `steer/thr/brk` + pad slot-nya (P1..P4).
- [ ] **Uji 2 HP.** Dua HP satu WiFi, dua pad muncul di `joy.cpl`,
      input tidak saling tukar (kirim bergantian + bersamaan).
- [ ] **Batas & penolakan.** IP ke-5+ ditolak dengan log jelas
      (XInput maks 4 pad). Pertimbangkan allowlist IP.

## V0.5 — Siap publikasi (belum mulai)
Syarat sebelum disebar ke publik:

- [ ] **Install reproducible.** `vgamepad==0.1.0` hanya sdist dan gagal build
      dengan pip/setuptools modern. Tentukan jalur resmi (wheel sendiri /
      pin setuptools / ganti library), hapus workaround salin-dari-system.
- [ ] **Lisensi redistribusi ViGEmBus 1.22.0** diklarifikasi (boleh bundle
      installer atau wajib link resmi). Tambah `LICENSE` repo.
- [ ] **Uji fresh-VM end-to-end 1x:** Windows bersih -> `--setup` (Admin) ->
      `joy.cpl` muncul Xbox 360 pad -> binding F1 2020 kebaca ->
      uninstall bersih (task + shortcut terhapus).
- [ ] **Paket rilis:** zip `BalapinBridge-<versi>.zip` berisi EXE + README
      singkat + SHA256 checksum + catatan SmartScreen/AV (tanpa code signing).
- [ ] **Firewall UDP 5005:** aturan inbound otomatis saat setup atau
      instruksi manual yang jelas.
- [ ] **Disclaimer keamanan:** UDP polos tanpa auth di LAN — main di jaringan
      pribadi saja (risiko inject input dari perangkat lain).
- [ ] **Versioning:** versi eksplisit di EXE (`--version`) + tag git per rilis.
