#!/usr/bin/env python3
"""Balapin PC UDP Bridge — monitor V0.2.

Menerima paket JSON dari HP Android (controller) via UDP dan menampilkan
nilai steering/throttle/brake, tombol ABXY, dan statistik koneksi.

Format paket yang diharapkan:
    {"steering": 0.65, "throttle": 0.0, "brake": 0.0,
     "buttons": 5, "race": 3, "seq": 123, "ts": 169...}
- steering: -1.0 ... +1.0
- throttle/brake: 0.0 ... 1.0
- buttons: bitmask A=1, B=2, X=4, Y=8
- race: bitmask DRS=1, ERS=2, ABS=4, TC=8, PIT_LIMIT=16, PIT_IN=32
- seq: nomor urut (deteksi packet loss)
- ts: epoch-ms di HP saat paket dibuat (ukur latency)

Stdlib only — tidak ada dependency. Wajib dijalankan di dalam venv:
    py -m venv .venv
    .\\.venv\\Scripts\\activate
    python udp_monitor.py --port 5005
"""

import argparse
import json
import socket
import sys
import time
from collections import deque


def decode_buttons(mask: int) -> str:
    """Ubah bitmask ABXY menjadi label yang mudah dibaca."""
    labels = [(0b0001, "A"), (0b0010, "B"),
              (0b0100, "X"), (0b1000, "Y")]
    active = [label for bit, label in labels if mask & bit]
    return "+".join(active) if active else "-"


def decode_race(mask: int) -> str:
    """Ubah bitmask race control menjadi label yang mudah dibaca."""
    labels = [
        (0b000001, "DRS"),
        (0b000010, "ERS"),
        (0b000100, "ABS"),
        (0b001000, "TC"),
        (0b010000, "PIT_LIMIT"),
        (0b100000, "PIT_IN"),
    ]
    active = [label for bit, label in labels if mask & bit]
    return "+".join(active) if active else "-"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Balapin UDP monitor (V0.2): terima + tampilkan data controller."
    )
    parser.add_argument("--host", default="0.0.0.0",
                        help="Interface listen (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=5005,
                        help="Port UDP listen (default: 5005)")
    parser.add_argument("--timeout", type=float, default=0.5,
                        help="Batas timeout detik untuk warning lost (default: 0.5)")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.bind((args.host, args.port))
    except OSError as exc:
        print(f"Gagal bind {args.host}:{args.port}: {exc}", file=sys.stderr)
        return 1
    sock.settimeout(args.timeout)

    print(f"Listening UDP {args.host}:{args.port} ... (Ctrl+C untuk stop)")
    print("Pastikan HP + PC satu WiFi dan firewall mengizinkan UDP port "
          f"{args.port}.")

    last_seq = None
    received = 0
    lost = 0
    latencies_ms = deque(maxlen=60)
    window_start = time.time()
    window_count = 0
    last_addr = None

    try:
        while True:
            try:
                data, addr = sock.recvfrom(4096)
            except socket.timeout:
                print(f"\rTIMEOUT: tidak ada paket > {args.timeout * 1000:.0f}ms "
                      f"(cek Connect di HP / IP / firewall)   ",
                      end="", flush=True)
                continue

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
            except (ValueError, KeyError, TypeError) as exc:
                print(f"\nPaket rusak dari {addr}: {exc}")
                continue

            received += 1
            window_count += 1
            last_addr = addr
            if last_seq is not None and seq > last_seq + 1:
                lost += seq - last_seq - 1
            last_seq = seq
            latencies_ms.append(now_ms - ts)

            elapsed = time.time() - window_start
            if elapsed >= 1.0:
                rate = window_count / elapsed
                avg_lat = (sum(latencies_ms) / len(latencies_ms)
                           if latencies_ms else 0.0)
                print(f"\rsteer={steer:+.3f} thr={thr:.2f} brk={brk:.2f} "
                      f"ABXY={decode_buttons(buttons)} "
                      f"RACE={decode_race(race)} | "
                      f"{rate:.0f} pkt/s rx={received} lost={lost} "
                      f"lat={avg_lat:.0f}ms dari {addr[0]}   ",
                      end="", flush=True)
                window_start = time.time()
                window_count = 0
    except KeyboardInterrupt:
        print(f"\nStop. received={received} lost={lost} "
              f"last_from={last_addr}")
        return 0
    finally:
        sock.close()


if __name__ == "__main__":
    raise SystemExit(main())
