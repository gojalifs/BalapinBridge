"""Auto-start BalapinBridge via Scheduled Task (mode user, ONLOGON).

Dipilih Task Scheduler (bukan true Windows Service/SYSTEM) karena:
- vgamepad + F1 2020 butuh sesi user yang sama (joy.cpl terlihat),
- tidak butuh pywin32 service wrapper / session-0 isolation,
- tetap bisa start/stop/status/uninstall dari EXE desktop.

Task:  BalapinBridge
Aksi:  "<exe>" --manual [--port ...]
Trigger: ONLOGON (user saat ini)
"""

from __future__ import annotations

import os
import subprocess
import sys

TASK_NAME = "BalapinBridge"


def _run(cmd: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True,
                          creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))


def get_own_command(extra_args: str = "--manual") -> str:
    """Perintah yang didaftarkan ke Task Scheduler."""
    if getattr(sys, "frozen", False):
        return f'"{sys.executable}" {extra_args}'
    # Mode source: "python <repo>/bridge_app.py --manual"
    py = sys.executable
    here = os.path.dirname(os.path.abspath(__file__))
    entry = os.path.join(here, "bridge_app.py")
    return f'"{py}" "{entry}" {extra_args}'


def is_installed() -> bool:
    r = _run(["schtasks", "/Query", "/TN", TASK_NAME])
    return r.returncode == 0


def get_status() -> str:
    """Return: not-installed | running | ready | unknown:<rc>."""
    r = _run(["schtasks", "/Query", "/TN", TASK_NAME, "/V", "/FO", "LIST"])
    if r.returncode != 0:
        # Fallback non-verbose (XP-style output beda bahasa)
        r2 = _run(["schtasks", "/Query", "/TN", TASK_NAME])
        return "not-installed" if r2.returncode != 0 else "unknown:0"
    blob = (r.stdout + r.stderr).lower()
    # Baris "Status:            Running" saat task sedang jalan.
    for line in blob.splitlines():
        if line.strip().startswith("status:"):
            return "running" if "running" in line else "ready"
    return "ready" if is_installed() else "not-installed"


def install_task(command: str | None = None) -> tuple[bool, str]:
    cmd = command or get_own_command()
    r = _run(["schtasks", "/Create", "/TN", TASK_NAME, "/TR", cmd,
              "/SC", "ONLOGON", "/RL", "LIMITED", "/F"])
    if r.returncode == 0:
        return True, f"Auto-start terpasang (ONLOGON): {cmd}"
    return False, (r.stderr or r.stdout or f"schtasks exit {r.returncode}").strip()


def uninstall_task() -> tuple[bool, str]:
    r = _run(["schtasks", "/Delete", "/TN", TASK_NAME, "/F"])
    if r.returncode == 0:
        return True, "Auto-start dihapus"
    return False, (r.stderr or r.stdout or f"schtasks exit {r.returncode}").strip()


def start_task() -> tuple[bool, str]:
    r = _run(["schtasks", "/Run", "/TN", TASK_NAME])
    if r.returncode == 0:
        return True, "Task dijalankan (cek tray/joy.cpl beberapa detik lagi)"
    return False, (r.stderr or r.stdout or f"schtasks exit {r.returncode}").strip()


def stop_task() -> tuple[bool, str]:
    r = _run(["schtasks", "/End", "/TN", TASK_NAME])
    if r.returncode == 0:
        return True, "Task dihentikan"
    return False, (r.stderr or r.stdout or f"schtasks exit {r.returncode}").strip()


def create_desktop_shortcut(exe_path: str | None = None,
                            name: str = "BalapinBridge.lnk") -> tuple[bool, str]:
    """Buat shortcut .lnk di Desktop ke EXE (via PowerShell WScript.Shell)."""
    target = exe_path or (sys.executable if getattr(sys, "frozen", False)
                          else os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                            "bridge_app.py"))
    desktop = os.path.join(os.path.expanduser("~"), "Desktop")
    lnk = os.path.join(desktop, name)
    ps = (f"$ws = New-Object -ComObject WScript.Shell; "
          f"$s = $ws.CreateShortcut('{lnk}'); "
          f"$s.TargetPath = '{target}'; $s.WorkingDirectory = "
          f"'{os.path.dirname(target)}'; $s.Save()")
    r = _run(["powershell", "-NoProfile", "-Command", ps])
    if r.returncode == 0 and os.path.exists(lnk):
        return True, f"Shortcut dibuat: {lnk}"
    return False, (r.stderr or r.stdout or "gagal buat shortcut").strip()
