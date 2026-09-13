#!/usr/bin/env python3
"""Production watchdog — set-and-forget health loop.

Polls /api/ready, writes alerts to ALERT_SINK_FILE / webhook (via API env),
and optionally restarts the RQ worker when workers drop to zero.

Usage (from repo root):
  set STAGING_URL=http://127.0.0.1:8000
  python ops/watchdog.py

Env:
  WATCHDOG_URL          default http://127.0.0.1:8000
  WATCHDOG_INTERVAL_SEC default 30
  WATCHDOG_RESTART_WORKER=1  restart worker when workers<1 (Windows/Unix)
  WATCHDOG_WORKER_CMD   override worker command
  ALERT_SINK_FILE       local JSONL alert log (also used if API settings point here)
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
URL = (os.environ.get("WATCHDOG_URL") or os.environ.get("STAGING_URL") or "http://127.0.0.1:8000").rstrip("/")
INTERVAL = max(10, int(os.environ.get("WATCHDOG_INTERVAL_SEC", "30")))
RESTART_WORKER = os.environ.get("WATCHDOG_RESTART_WORKER", "1") not in {"0", "false", "False"}
SINK = Path(os.environ.get("ALERT_SINK_FILE") or (ROOT / "ops" / "evidence" / "alerts.jsonl"))
WORKER_PID_FILE = ROOT / "ops" / "evidence" / "worker.pid"
STATE_FILE = ROOT / "ops" / "evidence" / "watchdog_state.json"


def utcnow() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def fetch_ready() -> tuple[int, dict]:
    req = urllib.request.Request(f"{URL}/api/ready", method="GET")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return int(resp.status), json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        try:
            body = json.loads(raw) if raw else {}
        except json.JSONDecodeError:
            body = {"raw": raw[:300]}
        return int(exc.code), body
    except Exception as exc:  # noqa: BLE001
        return 0, {"error": str(exc), "ready": False}


def alert(title: str, detail: str, severity: str = "critical") -> None:
    SINK.parent.mkdir(parents=True, exist_ok=True)
    row = {
        "ts": utcnow(),
        "source": "watchdog",
        "severity": severity,
        "title": title,
        "detail": detail,
        "url": URL,
    }
    with SINK.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row) + "\n")
    print(f"[{severity}] {title}: {detail}", flush=True)


def save_state(payload: dict) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def restart_worker() -> None:
    if not RESTART_WORKER:
        return
    cmd = os.environ.get("WATCHDOG_WORKER_CMD")
    if not cmd:
        py = ROOT / "backend" / ".venv" / "Scripts" / "python.exe"
        if not py.exists():
            py = Path(sys.executable)
        cmd = f'"{py}" -m app.workers.rq_worker'
    # Stop previous supervised worker if we tracked it.
    if WORKER_PID_FILE.exists():
        try:
            old = int(WORKER_PID_FILE.read_text(encoding="utf-8").strip() or "0")
            if old > 0 and os.name == "nt":
                subprocess.run(["taskkill", "/PID", str(old), "/F"], check=False, capture_output=True)
            elif old > 0:
                os.kill(old, 15)
        except Exception:  # noqa: BLE001
            pass
    creationflags = 0
    if os.name == "nt":
        creationflags = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS  # type: ignore[attr-defined]
    proc = subprocess.Popen(
        cmd if os.name == "nt" else cmd.split(),
        cwd=str(ROOT / "backend"),
        shell=(os.name == "nt"),
        creationflags=creationflags,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    WORKER_PID_FILE.write_text(str(proc.pid), encoding="utf-8")
    alert("worker_restarted", f"Started worker pid={proc.pid}", severity="warning")


def main() -> int:
    print(f"watchdog targeting {URL} every {INTERVAL}s sink={SINK}", flush=True)
    fail_streak = 0
    while True:
        status, body = fetch_ready()
        ready = bool(body.get("ready")) and status == 200
        workers = body.get("workers")
        redis_ok = body.get("redis")
        state = {
            "checked_at": utcnow(),
            "http_status": status,
            "ready": ready,
            "workers": workers,
            "redis": redis_ok,
            "body": body,
            "fail_streak": fail_streak,
        }
        save_state(state)
        if ready and (workers is None or int(workers or 0) >= 1):
            if fail_streak:
                alert("ready_recovered", f"Ready restored after {fail_streak} failures", severity="info")
            fail_streak = 0
        else:
            fail_streak += 1
            detail = f"status={status} ready={ready} redis={redis_ok} workers={workers} body={body}"
            alert("ready_failed", detail, severity="critical")
            if redis_ok and (workers is None or int(workers or 0) < 1):
                restart_worker()
        time.sleep(INTERVAL)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("watchdog stopped", flush=True)
        raise SystemExit(0)
