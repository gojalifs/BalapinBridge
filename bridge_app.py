#!/usr/bin/env python3
"""BalapinBridge EXE — satu entry untuk setup + desktop controller.

Perilaku:
- Tanpa argumen (klik dari Desktop):
    * task terinstal + running -> info "service sudah jalan", exit.
    * task terinstal + belum jalan -> jalankan task (schtasks /Run), info.
    * task tidak terinstal          -> jalankan bridge manual foreground.
- --setup: cek ViGEmBus (skip bila ada, install /qn bila belum),
  lalu minta persetujuan user untuk pasang auto-start (tidak otomatis).
- --manual: jalankan bridge loop (dipakai Task Scheduler + fallback manual).
- --status / --install-autostart / --uninstall-autostart / --start / --stop:
  kelola task secara eksplisit.
"""

from __future__ import annotations

import argparse
import sys
import threading

import autostart
import udp_to_gamepad
import vigembus


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="BalapinBridge (setup + desktop controller).")
    p.add_argument("--version", action="store_true",
                   help="Tampilkan versi aplikasi")
    p.add_argument("--setup", action="store_true",
                   help="Jalankan bridge foreground (dipakai task + fallback)")
    p.add_argument("--status", action="store_true", help="Tampilkan status driver + task")
    p.add_argument("--install-autostart", action="store_true",
                   help="Pasang auto-start ONLOGON (tanpa tanya)")
    p.add_argument("--uninstall-autostart", action="store_true", help="Hapus auto-start")
    p.add_argument("--start", action="store_true", help="Jalankan task sekarang")
    p.add_argument("--stop", action="store_true", help="Hentikan task")
    p.add_argument("--port", type=int, default=5005)
    p.add_argument("--host", default="0.0.0.0")
    p.add_argument("--timeout", type=float, default=0.5)
    p.add_argument("--rate", type=float, default=60.0)
    p.add_argument("--dry-run", action="store_true",
                   help="Tanpa driver, hanya log (debug)")
    p.add_argument("--yes", action="store_true",
                   help="Jawab Ya otomatis untuk prompt (skrip)")
    return p


def cmd_status() -> int:
    drv_ok, drv_msg = vigembus.is_vigembus_installed()
    print(f"Driver ViGEmBus : {'OK' if drv_ok else 'BELUM'} — {drv_msg}")
    print(f"Auto-start task : {autostart.get_status()} "
          f"(task: {autostart.TASK_NAME})")
    log = udp_to_gamepad.get_log_file()
    print(f"Log file        : {log or '-'}")
    return 0


def ask_yes_no(prompt: str, auto_yes: bool = False) -> bool:
    if auto_yes:
        print(f"{prompt} [auto: Ya]")
        return True
    try:
        ans = input(f"{prompt} [y/N]: ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        print()
        return False
    return ans in ("y", "ya", "yes")


def cmd_setup(args: argparse.Namespace) -> int:
    print("=== BalapinBridge setup ===")
    ok, msg = vigembus.is_vigembus_installed()
    if ok:
        print(f"[driver] {msg} -> skip install.")
    else:
        print(f"[driver] {msg}")
        if not ask_yes_no("Driver belum ada. Install ViGEmBus sekarang?", args.yes):
            print("Setup dibatalkan (driver wajib untuk mode gamepad).")
            return 1
        print("Menginstall ViGEmBus (silent /qn, butuh Admin)...")
        ok2, msg2 = vigembus.install_vigembus_silent()
        print(f"[driver] {msg2}")
        if not ok2:
            return 1
    
    # Tambahkan aturan firewall UDP 5005 setelah driver terinstall
    print("[firewall] Menambahkan aturan inbound UDP 5005...")
    try:
        import subprocess
        result = subprocess.run(
            ["netsh", "advfirewall", "firewall", "add", "rule",
             "name=Balapin PC Bridge UDP 5005", "dir=in", "action=allow",
             "protocol=UDP", "localport=5005"],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            print("[firewall] Aturan UDP 5005 berhasil ditambahkan.")
        else:
            print("[firewall] Gagal menambahkan aturan (mungkin sudah ada):")
            print(result.stderr)
    except Exception as e:
        print(f"[firewall] Error saat setup aturan: {e}")
    
    # Auto-start TIDAK otomatis — wajib persetujuan user.
    print(f"\nAuto-start saat ini: {autostart.get_status()}")
    if autostart.is_installed():
        print("Auto-start sudah terpasang. Selesai.")
    elif ask_yes_no("Pasang auto-start (jalan otomatis saat Windows login)?", args.yes):
        ok3, msg3 = autostart.install_task()
        print(f"[autostart] {msg3}")
        if ok3:
            ok4, msg4 = autostart.create_desktop_shortcut()
            print(f"[shortcut] {msg4}")
        return 0 if ok3 else 1
    else:
        print("Dilewati: bridge tetap bisa dijalankan manual dari EXE ini.")
    ok4, msg4 = autostart.create_desktop_shortcut()
    print(f"[shortcut] {msg4}")
    print("\nSetup selesai. Cek joy.cpl lalu binding di F1 2020.")
    return 0


def cmd_desktop_default(args: argparse.Namespace) -> int:
    """Logika EXE Desktop: running->info, ready->start, hilang->manual."""
    state = autostart.get_status()
    if state == "running":
        print("BalapinBridge service SUDAH JALAN (task Running). "
              "Tidak perlu aksi. Tutup jendela ini bila hanya mengecek.")
        print("Tips: kirim paket dari HP, atau jalankan --status untuk detail.")
        return 0
    if state == "ready":
        print("Auto-start terinstal tapi belum jalan. Menjalankan task...")
        ok, msg = autostart.start_task()
        print(msg)
        return 0 if ok else 1
    # not-installed / unknown -> manual foreground dari EXE ini
    print("Auto-start TIDAK terinstal — menjalankan bridge MANUAL dari EXE ini.")
    print("(Pasang auto-start kapan saja via: BalapinBridge.exe --setup)")
    stop = threading.Event()
    return udp_to_gamepad.run_bridge(host=args.host, port=args.port,
                                     timeout=args.timeout, rate=args.rate,
                                     dry_run=args.dry_run, stop_event=stop)


def cmd_version() -> int:
    print("BalapinBridge versione 0.3.0")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.setup:
        return cmd_setup(args)
    if args.status:
        return cmd_status()
    if args.install_autostart:
        ok, msg = autostart.install_task()
        print(msg)
        return 0 if ok else 1
    if args.uninstall_autostart:
        ok, msg = autostart.uninstall_task()
        print(msg)
        return 0 if ok else 1
    if args.start:
        ok, msg = autostart.start_task()
        print(msg)
        return 0 if ok else 1
    if args.stop:
        ok, msg = autostart.stop_task()
        print(msg)
        return 0 if ok else 1
    if args.version:
        return cmd_version()
    if args.manual:
        stop = threading.Event()
        return udp_to_gamepad.run_bridge(host=args.host, port=args.port,
                                         timeout=args.timeout, rate=args.rate,
                                         dry_run=args.dry_run, stop_event=stop)
    return cmd_desktop_default(args)


if __name__ == "__main__":
    raise SystemExit(main())
