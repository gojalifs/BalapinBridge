"""Cek + install driver ViGEmBus (dipakai BalapinSetup / bridge_app --setup).

Urutan cek (cepat -> fungsional):
1. File driver ViGEmBus.sys
2. Registry Services\\ViGEmBus
3. Fungsional: VG.VX360Gamepad() — satu-satunya bukti pad bisa dibuka.
"""

from __future__ import annotations

import ctypes
import os
import subprocess
import sys

INSTALLER_REL = os.path.join("drivers", "ViGEmBus", "ViGEmBus_1.22.0_x64_x86_arm64.exe")
DRIVER_SYS = r"C:\Windows\System32\drivers\ViGEmBus.sys"


def is_admin() -> bool:
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def _driver_file_exists() -> bool:
    return os.path.exists(DRIVER_SYS)


def _registry_key_exists() -> bool:
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                            r"SYSTEM\CurrentControlSet\Services\ViGEmBus"):
            return True
    except (OSError, ImportError):
        return False


def functional_check() -> tuple[bool, str]:
    """Coba buka virtual pad. Return (ok, pesan)."""
    try:
        import vgamepad as VG
    except ImportError:
        return False, "vgamepad belum terinstall (pip install -r requirements.txt)"
    try:
        pad = VG.VX360Gamepad()
        try:
            del pad
        except Exception:
            pass
        return True, "ViGEmBus OK (VX360Gamepad bisa dibuka)"
    except Exception as exc:
        return False, f"ViGEmBus tidak bisa dipakai: {exc}"


def is_vigembus_installed() -> tuple[bool, str]:
    ok, msg = functional_check()
    if ok:
        return True, msg
    # Beri konteks kenapa gagal (file/registry hilang?)
    hints = []
    if not _driver_file_exists():
        hints.append("ViGEmBus.sys tidak ditemukan")
    if not _registry_key_exists():
        hints.append("registry ViGEmBus tidak ditemukan")
    detail = f"{msg}" + (f" ({'; '.join(hints)})" if hints else "")
    return False, detail


def _installer_path() -> str:
    if getattr(sys, "frozen", False):
        base = os.path.dirname(sys.executable)
        # PyInstaller onefile: data ikut via --add-data ke sys._MEIPASS
        meipass = getattr(sys, "_MEIPASS", base)
        for cand in (os.path.join(meipass, "drivers", "ViGEmBus",
                                  "ViGEmBus_1.22.0_x64_x86_arm64.exe"),
                     os.path.join(base, INSTALLER_REL),
                     os.path.abspath(INSTALLER_REL)):
            if os.path.exists(cand):
                return cand
        return os.path.join(meipass, "drivers", "ViGEmBus",
                            "ViGEmBus_1.22.0_x64_x86_arm64.exe")
    # Mode source: relatif ke repo root (file ini di root)
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(here, INSTALLER_REL)


def install_vigembus_silent() -> tuple[bool, str]:
    """Jalankan installer vendor dengan /qn. Wajib Admin. Return (ok, pesan)."""
    exe = _installer_path()
    if not os.path.exists(exe):
        return False, f"Installer tidak ketemu: {exe}"
    if not is_admin():
        return False, "Butuh Run as Administrator untuk install driver"
    try:
        # /qn = silent (lihat drivers/ViGEmBus/README.md). Tunggu sampai selesai.
        rc = subprocess.run([exe, "/qn"], check=False).returncode
    except Exception as exc:
        return False, f"Gagal menjalankan installer: {exc}"
    if rc != 0:
        return False, f"Installer exit code {rc} (coba jalankan 2x — bug upstream)"
    ok, msg = functional_check()
    if ok:
        return True, "ViGEmBus terinstall & terverifikasi (joy.cpl siap)"
    return False, (f"Installer selesai tapi verifikasi gagal: {msg}. "
                   "Coba reboot / jalankan installer 2x lalu cek joy.cpl")


def ensure_vigembus(auto_install: bool = False) -> tuple[bool, str]:
    ok, msg = is_vigembus_installed()
    if ok:
        return True, f"skip install — {msg}"
    if not auto_install:
        return False, msg
    return install_vigembus_silent()
