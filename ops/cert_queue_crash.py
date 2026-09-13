"""Kill Redis while jobs are queued; confirm AOF restores the queue (not silent drop).

Two consecutive crash → start cycles. Sentinel/Cluster failover remains UNPROVEN.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

REDIS_URL = os.environ.get("CERT_REDIS_URL", "redis://127.0.0.1:56379/0")
CONTAINER = os.environ.get("CERT_REDIS_CONTAINER", "aiessayassignmentchecker-redis-1")
os.environ["REDIS_URL"] = REDIS_URL
os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("APP_SECRET_KEY", "cert-secret")
os.environ.setdefault("JWT_SECRET_KEY", "cert-jwt-secret-key-32-bytes-min")

from redis import Redis  # noqa: E402
from rq import Queue  # noqa: E402


def docker(*args: str, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(["docker", *args], check=check, capture_output=True, text=True)


def wait_ping(client: Redis, timeout: int = 45) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            if client.ping():
                return True
        except Exception:
            time.sleep(0.5)
    return False


def cycle() -> dict:
    client = Redis.from_url(REDIS_URL, socket_timeout=2, socket_connect_timeout=2)
    if not wait_ping(client):
        return {"ok": False, "error": "redis unreachable before enqueue"}
    info = client.info("persistence")
    queue = Queue("dr_crash", connection=client)
    queue.empty()
    job_ids = []
    for i in range(12):
        job = queue.enqueue("app.workers.tasks.cert_ping", i)
        job_ids.append(job.id)
    queued = queue.count
    # appendfsync everysec — wait so AOF has the writes
    time.sleep(2.2)
    docker("kill", CONTAINER)
    time.sleep(1)
    docker("start", CONTAINER)
    client = Redis.from_url(REDIS_URL, socket_timeout=2, socket_connect_timeout=2)
    ping_ok = wait_ping(client)
    queue = Queue("dr_crash", connection=client)
    after = queue.count if ping_ok else -1
    recovered_ids = [job.id for job in queue.jobs] if ping_ok else []
    missing = sorted(set(job_ids) - set(recovered_ids))
    return {
        "aof_enabled": bool(info.get("aof_enabled")),
        "queued_before_kill": queued,
        "queued_after_restart": after,
        "missing_job_ids": missing,
        "lost_job_count": len(missing),
        "ping_after_restart": ping_ok,
        "ok": ping_ok and after == queued and not missing,
    }


def main() -> int:
    runs = [cycle(), cycle()]
    payload = {
        "measured_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "container": CONTAINER,
        "kill_signal": "docker kill (SIGKILL)",
        "consecutive_runs": 2,
        "runs": runs,
        "pass": all(run.get("ok") for run in runs),
        "sentinel_failover": "UNPROVEN",
        "note": "Volume retained. Redis volume-loss (down -v) still UNPROVEN.",
    }
    out = ROOT / "ops" / "cert_queue_crash.json"
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps({"pass": payload["pass"], "runs": runs}, indent=2))
    return 0 if payload["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
