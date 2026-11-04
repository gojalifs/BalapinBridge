"""Balapin converter (V0.3) — konektor & konverter murni, tanpa filter.

Kontrak input dari client Android (60 pkt/detik, JSON satu baris):
    {"steering":0.65,"throttle":0.0,"brake":0.0,"buttons":5,"race":3,"seq":123,"ts":172...}
- steering: -1.0 ... +1.0 (sudah termasuk deadzone/sensitivitas/filter di HP)
- throttle/brake: 0.0 ... 1.0
- buttons: bitmask A=1, B=2, X=4, Y=8
- seq: nomor urut (deteksi loss di bridge)
- ts: epoch-ms di HP (hitung latency di bridge)

Modul ini HANYA clamp + konversi ke range vgamepad float:
- steering -> left stick X -1.0 ... +1.0
- throttle -> right trigger 0.0 ... 1.0
- brake    -> left trigger  0.0 ... 1.0

Tidak ada deadzone/sensitivitas/smoothing di sini (milik client).
"""

from __future__ import annotations


def clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, float(value)))


def clamp_steering(value: float) -> float:
    return clamp(value, -1.0, 1.0)


def clamp_pedal(value: float) -> float:
    return clamp(value, 0.0, 1.0)


def convert(steering: float, throttle: float, brake: float) -> tuple[float, float, float]:
    """Kembalikan (steer_f, thr_f, brk_f) yang siap ke vgamepad *_float()."""
    return (
        clamp_steering(steering),
        clamp_pedal(throttle),
        clamp_pedal(brake),
    )


def steering_to_xinput(steering: float) -> int:
    """Helper logging/test: -1..+1 -> -32768..+32767 (XInput)."""
    s = clamp_steering(steering)
    return -32768 if s <= -1.0 else int(round(s * 32767))


def pedal_to_xinput(pedal: float) -> int:
    """Helper logging/test: 0..1 -> 0..255 (trigger)."""
    return int(round(clamp_pedal(pedal) * 255))
