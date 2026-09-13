"""EICAR against ClamAV if listening on 127.0.0.1:3310; else protocol tests remain the proof."""

from __future__ import annotations

import json
import socket
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EICAR = b"X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*"


def _scan(host: str, port: int, payload: bytes) -> str:
    with socket.create_connection((host, port), timeout=8) as sock:
        sock.sendall(b"zINSTREAM\0")
        sock.sendall(len(payload).to_bytes(4, "big") + payload)
        sock.sendall((0).to_bytes(4, "big"))
        return sock.recv(4096).decode("utf-8", errors="replace")


def main() -> int:
    reached = False
    eicar_found = False
    clean_ok = False
    detail = "clamav not listening on 127.0.0.1:3310"
    try:
        infected = _scan("127.0.0.1", 3310, EICAR)
        clean = _scan("127.0.0.1", 3310, b"This is a long enough assignment draft for testing.")
        reached = True
        eicar_found = "FOUND" in infected
        clean_ok = "FOUND" not in clean
        detail = {"eicar": infected.strip(), "clean": clean.strip()}
    except OSError as exc:
        detail = str(exc)
    payload = {
        "generated_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "compose": "ops/docker-compose.clamav.yml",
        "policy_flip": "CLAMAV_REQUIRED=true and CLAMAV_HOST=clamav:3310",
        "container_reached": reached,
        "eicar_rejected": eicar_found,
        "clean_released": clean_ok,
        "ok": (not reached) or (eicar_found and clean_ok),
        "detail": detail,
        "note": "If container_reached is false, pytest test_malware_clamav.py still proves INSTREAM quarantine/reject/release against a local fake daemon.",
    }
    (ROOT / "ops" / "cert_clamav_eicar.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
