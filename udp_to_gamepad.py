#!/usr/bin/env python3
"""Balapin PC Bridge V0.3 — UDP -> ViGEm Xbox 360 pad.

Konektor & konverter murni (tanpa filter):
- Terima JSON dari HP: {"steering":..,"throttle":..,"brake":..,"buttons":..,"race":..,"seq":..,"ts":..}
- Clamp via converter.py, teruskan ke virtual Xbox pad (vgamepad):
    steering -> LeftStick-X, throttle -> RightTrigger, brake -> LeftTrigger
    buttons -> A/B/X/Y (bitmask 1/2/4/8)
    race -> DPAD_UP/DPAD_DOWN/LEFT_SHOULDER/RIGHT_SHOULDER/BACK/START
- Mapping race: DRS=DPAD_UP, ERS=DPAD_DOWN, ABS=LB, TC=RB,
  PIT_LIMIT=BACK, PIT_IN=START.
- Failsafe: jika tidak ada paket > --timeout detik, kirim netral (0,0,0,0).
- Statistik: pkt/s, rx, lost (dari seq), latency (now - ts).

Prasyarat (sekali saja):
    drivers\\ViGEmBus\\ViGEmBus_1.22.0_x64_x86_arm64.exe  (sudah di-vendor di repo)
    pip install -r requirements.txt   (butuh vgamepad)

Contoh:
    python udp_to_gamepad.py --port 5005
    python udp_to_gamepad.py --port 5005 --dry-run   # tanpa driver, hanya log
"""

from __future__ import annotations

import argparse
import json
import socket
import sys
import threading
import time
from collections import deque
from dataclasses import dataclass

from converter import convert


LOG_DIR_CANDIDATES = []
try:
    _pd = __import__("os").environ.get("ProgramData")
    if _pd:
        LOG_DIR_CANDIDATES.append(__import__("os").path.join(_pd, "Balapin"))
except Exception:
    pass
try:
    import tempfile
    LOG_DIR_CANDIDATES.append(__import__("os").path.join(tempfile.gettempdir(), "Balapin"))
except Exception:
    pass


def get_log_file() -> str | None:
    import os
    for d in LOG_DIR_CANDIDATES:
        try:
            os.makedirs(d, exist_ok=True)
            p = os.path.join(d, "bridge.log")
            with open(p, "a", encoding="utf-8"):
                pass
            return p
        except OSError:
            continue
    return None


def log_line(msg: str) -> None:
    print(msg, flush=True)
    path = get_log_file()
    if path:
        try:
            with open(path, "a", encoding="utf-8") as f:
                f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} {msg}\n")
        except OSError:
            pass


def decode_buttons(mask: int) -> str:
    labels = ((0b0001, "A"), (0b0010, "B"),
              (0b0100, "X"), (0b1000, "Y"))
    active = [label for bit, label in labels if mask & bit]
    return "+".join(active) if active else "-"


def decode_race(mask: int) -> str:
    labels = (
        (0b000001, "DRS"),
        (0b000010, "ERS"),
        (0b000100, "ABS"),
        (0b001000, "TC"),
        (0b010000, "PIT_LIMIT"),
        (0b100000, "PIT_IN"),
    )
    active = [label for bit, label in labels if mask & bit]
    return "+".join(active) if active else "-"


@dataclass
class Latest:
    steering: float = 0.0
    throttle: float = 0.0
    brake: float = 0.0
    buttons: int = 0
    race: int = 0
    seq: int = -1
    ts: float = 0.0
    recv_wall: float = 0.0
    has_data: bool = False


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Balapin UDP->Gamepad bridge (V0.3).")
    p.add_argument("--host", default="0.0.0.0")
    p.add_argument("--port", type=int, default=5005)
    p.add_argument("--timeout", type=float, default=0.5,
                   help="Detik tanpa paket sebelum failsafe netral (default: 0.5)")
    p.add_argument("--rate", type=float, default=60.0,
                   help="Hz pengiriman ke virtual pad (default: 60)")
    p.add_argument("--dry-run", action="store_true",
                   help="Jangan sentuh driver, hanya tampilkan hasil konversi")
    return p.parse_args()


def receiver_loop(sock: socket.socket, latest: Latest, lock: threading.Lock,
                  stats: dict, stop: threading.Event) -> None:
    while not stop.is_set():
        try:
            data, addr = sock.recvfrom(4096)
        except socket.timeout:
            continue
        except OSError:
            break
        now_ms = time.time() * 1000.0
        try:
            msg = json.loads(data.decode("utf-8"))
            steer = float(msg["steering"])
            thr = float(msg.get("throttle", 0.0))
            brk = float(msg.get("brake", 0.0))
            buttons = int(msg.get("buttons", 0))
            race = int(msg.get("race", 0))
            seq = int(msg.get("seq", -1))
            ts = float(msg.get("ts", now_ms))
        except (ValueError, KeyError, TypeError):
            stats["bad"] += 1
            continue
        with lock:
            if latest.has_data and seq > latest.seq + 1 and latest.seq >= 0 and seq >= 0:
                stats["lost"] += seq - latest.seq - 1
            latest.steering, latest.throttle, latest.brake = convert(steer, thr, brk)
            latest.buttons = buttons
            latest.race = race
            latest.seq = seq
            latest.ts = ts
            latest.recv_wall = time.time()
            latest.has_data = True
            stats["received"] += 1
            stats["lat_ms"].append(now_ms - ts)
            stats["addr"] = addr[0]


def apply_mask_buttons(gamepad, bindings, mask: int, previous: int) -> None:
    """Terapkan hanya perubahan bit button ke virtual Xbox pad."""
    for bit, button in bindings:
        active = bool(mask & bit)
        was_active = bool(previous & bit)
        if active and not was_active:
            gamepad.press_button(button=button)
        elif was_active and not active:
            gamepad.release_button(button=button)


def open_gamepad(dry_run: bool):
    """Buka VX360 pad. Return (gamepad, VG, button_bindings, race_bindings).

    Raise RuntimeError dengan pesan user-friendly jika driver gagal.
    """
    if dry_run:
        return None, None, (), ()
    try:
        import vgamepad as VG
    except ImportError as exc:
        raise RuntimeError(
            "vgamepad belum terinstall. Jalankan: pip install -r requirements.txt"
        ) from exc
    try:
        gamepad = VG.VX360Gamepad()
        button_bindings = (
            (0b0001, VG.XUSB_BUTTON.XUSB_GAMEPAD_A),
            (0b0010, VG.XUSB_BUTTON.XUSB_GAMEPAD_B),
            (0b0100, VG.XUSB_BUTTON.XUSB_GAMEPAD_X),
            (0b1000, VG.XUSB_BUTTON.XUSB_GAMEPAD_Y),
        )
        race_bindings = (
            (0b000001, VG.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_UP),
            (0b000010, VG.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_DOWN),
            (0b000100, VG.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_SHOULDER),
            (0b001000, VG.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_SHOULDER),
            (0b010000, VG.XUSB_BUTTON.XUSB_GAMEPAD_BACK),
            (0b100000, VG.XUSB_BUTTON.XUSB_GAMEPAD_START),
        )
        return gamepad, VG, button_bindings, race_bindings
    except Exception as exc:
        raise RuntimeError(
            f"Gagal buka virtual pad: {exc}. "
            "Install dulu: drivers\\ViGEmBus\\ViGEmBus_1.22.0_x64_x86_arm64.exe"
        ) from exc


def run_bridge(host: str = "0.0.0.0", port: int = 5005,
               timeout: float = 0.5, rate: float = 60.0,
               dry_run: bool = False,
               stop_event: threading.Event | None = None,
               quiet: bool = False) -> int:
    """Jalankan loop bridge. Bisa dihentikan via stop_event (untuk task/service).

    Return 0 sukses, 1 bind gagal, 2/3 gamepad gagal. Tetap kompatibel
    dengan perilaku main() lama (Ctrl+C -> stop bersih + failsafe netral).
    """
    try:
        gamepad, _, button_bindings, race_bindings = open_gamepad(dry_run)
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 3 if "virtual pad" in str(exc) else 2

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.bind((host, port))
    except OSError as exc:
        print(f"Gagal bind {host}:{port}: {exc}", file=sys.stderr)
        return 1
    sock.settimeout(0.2)

    latest = Latest()
    lock = threading.Lock()
    stop = stop_event or threading.Event()
    internal_stop = stop_event is None
    stats = {"received": 0, "lost": 0, "bad": 0,
             "lat_ms": deque(maxlen=60), "addr": "-"}
    thread = threading.Thread(target=receiver_loop,
                              args=(sock, latest, lock, stats, stop),
                              daemon=True)
    thread.start()

    period = 1.0 / max(1.0, rate)
    if not quiet:
        log_line(f"Bridge UDP {host}:{port} -> "
                 f"{'DRY-RUN' if dry_run else 'VX360 pad'} @ {rate:.0f}Hz "
                 f"(Ctrl+C stop, failsafe {timeout * 1000:.0f}ms)")
    window_start = time.time()
    window_sent = 0
    last_sent_buttons = 0
    last_sent_race = 0
    try:
        while not stop.is_set():
            tick = time.time()
            with lock:
                age = tick - latest.recv_wall if latest.has_data else 999.0
                if latest.has_data and age <= timeout:
                    s, t, b = latest.steering, latest.throttle, latest.brake
                    buttons = latest.buttons
                    race = latest.race
                    live = True
                else:
                    s, t, b = 0.0, 0.0, 0.0
                    buttons = 0
                    race = 0
                    live = False
                lat = (sum(stats["lat_ms"]) / len(stats["lat_ms"])
                       if stats["lat_ms"] else 0.0)
                rx, lost, addr = stats["received"], stats["lost"], stats["addr"]
            if gamepad is not None:
                gamepad.left_joystick_float(x_value_float=s, y_value_float=0.0)
                gamepad.right_trigger_float(value_float=t)
                gamepad.left_trigger_float(value_float=b)
                apply_mask_buttons(
                    gamepad, button_bindings or (), buttons, last_sent_buttons
                )
                apply_mask_buttons(
                    gamepad, race_bindings or (), race, last_sent_race
                )
                last_sent_buttons = buttons
                last_sent_race = race
                gamepad.update()
            window_sent += 1
            elapsed = time.time() - window_start
            if elapsed >= 1.0 and not quiet:
                rate_out = window_sent / elapsed
                state = "LIVE " if live else "HOLD-NEUTRAL"
                button_text = decode_buttons(buttons)
                race_text = decode_race(race)
                print(f"\r[{state}] steer={s:+.3f} thr={t:.2f} brk={b:.2f} "
                      f"ABXY={button_text} RACE={race_text} | "
                      f"out={rate_out:.0f}/s rx={rx} lost={lost} "
                      f"lat={lat:.0f}ms dari {addr}   ",
                      end="", flush=True)
                window_start = time.time()
                window_sent = 0
            delay = period - (time.time() - tick)
            if delay > 0:
                if stop.wait(delay):
                    break
    except KeyboardInterrupt:
        pass
    finally:
        if internal_stop:
            stop.set()
        try:
            sock.close()
        except OSError:
            pass
        if not quiet:
            print(f"\nStop. rx={stats['received']} lost={stats['lost']} bad={stats['bad']}")
    return 0


def main() -> int:
    args = parse_args()
    return run_bridge(host=args.host, port=args.port, timeout=args.timeout,
                      rate=args.rate, dry_run=args.dry_run)


if __name__ == "__main__":
    raise SystemExit(main())
