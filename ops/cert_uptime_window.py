"""Record a short measured availability window. Does not invent 7/30/90-day SLO."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
PORT = 8035
PG = os.environ.get(
    "CERT_DATABASE_URL",
    "postgresql+psycopg://academiccheck:academiccheck@127.0.0.1:55432/academiccheck",
)
REDIS = os.environ.get("CERT_REDIS_URL", "redis://127.0.0.1:56379/0")
SECONDS = int(os.environ.get("CERT_UPTIME_SECONDS", "60"))


def probe() -> tuple[int | None, int | None]:
    live = ready = None
    try:
        with urlopen(f"http://127.0.0.1:{PORT}/api/live", timeout=2) as resp:
            live = resp.status
    except Exception:
        live = None
    try:
        with urlopen(f"http://127.0.0.1:{PORT}/api/ready", timeout=3) as resp:
            ready = resp.status
    except Exception as exc:
        ready = int(exc.code) if hasattr(exc, "code") else None
    return live, ready


def main() -> int:
    env = os.environ.copy()
    env.update(
        {
            "APP_ENV": "test",
            "DATABASE_URL": PG,
            "REDIS_URL": REDIS,
            "APP_SECRET_KEY": "cert-secret",
            "JWT_SECRET_KEY": "cert-jwt-secret-key-32-bytes-min",
            "PYTHONPATH": str(BACKEND),
        }
    )
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", str(PORT)],
        cwd=BACKEND,
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    samples = []
    try:
        deadline = time.time() + 30
        while time.time() < deadline:
            live, _ = probe()
            if live == 200:
                break
            time.sleep(0.2)
        end = time.time() + SECONDS
        while time.time() < end:
            live, ready = probe()
            samples.append({"t": time.time(), "live": live, "ready": ready})
            time.sleep(1)
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
    live_ok = sum(1 for s in samples if s["live"] == 200)
    ready_ok = sum(1 for s in samples if s["ready"] == 200)
    n = len(samples)
    payload = {
        "measured_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "window_s": SECONDS,
        "samples": n,
        "live_200": live_ok,
        "ready_200": ready_ok,
        "live_availability": round(live_ok / n, 6) if n else 0,
        "ready_availability": round(ready_ok / n, 6) if n else 0,
        "days_7": "not_measured",
        "days_30": "not_measured",
        "days_90": "not_measured",
        "slo_99_95_supported": False,
    }
    out = ROOT / "ops" / "cert_uptime_window.json"
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
