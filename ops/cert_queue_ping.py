"""RQ ping volume. Certifies Redis/RQ enqueue+complete, not full analysis."""

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

REDIS = os.environ.get("CERT_REDIS_URL", "redis://127.0.0.1:56379/0")
JOBS = int(os.environ.get("CERT_PING_JOBS", "10000"))
WORKERS = int(os.environ.get("CERT_QUEUE_WORKERS", "5"))
PG = os.environ.get(
    "CERT_DATABASE_URL",
    "postgresql+psycopg://academiccheck:academiccheck@127.0.0.1:55432/academiccheck",
)

os.environ["DATABASE_URL"] = PG
os.environ["REDIS_URL"] = REDIS
os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("APP_SECRET_KEY", "cert-secret")
os.environ.setdefault("JWT_SECRET_KEY", "cert-jwt-secret-key-32-bytes-min")

from redis import Redis  # noqa: E402
from rq import Queue, Worker  # noqa: E402


def main() -> int:
    redis = Redis.from_url(REDIS, socket_timeout=10, socket_connect_timeout=10)
    redis.ping()
    # Isolated cert Redis (port 56379). Drop leftover RQ keys so volume counts are not mixed with prior runs.
    for key in redis.scan_iter("rq:*"):
        redis.delete(key)
    env = os.environ.copy()
    env.update(
        {
            "DATABASE_URL": PG,
            "REDIS_URL": REDIS,
            "APP_ENV": "test",
            "APP_SECRET_KEY": "cert-secret",
            "JWT_SECRET_KEY": "cert-jwt-secret-key-32-bytes-min",
            "PYTHONPATH": str(BACKEND),
        }
    )
    log_dir = ROOT / "tmp" / "cert_ping_workers"
    log_dir.mkdir(parents=True, exist_ok=True)
    procs = []
    for i in range(WORKERS):
        log = (log_dir / f"worker-{i}.log").open("w", encoding="utf-8")
        procs.append(
            subprocess.Popen(
                [sys.executable, "-m", "app.workers.rq_worker"],
                cwd=BACKEND,
                env=env,
                stdout=log,
                stderr=log,
            )
        )
    deadline = time.time() + 20
    workers = []
    while time.time() < deadline:
        workers = Worker.all(connection=redis)
        if workers:
            break
        time.sleep(0.3)
    if not workers:
        for proc in procs:
            proc.terminate()
        print("UNPROVEN: workers did not register")
        return 2

    redis.delete("cert:ping:done")
    queue = Queue("analysis", connection=redis)
    t0 = time.perf_counter()
    for i in range(JOBS):
        job_id = f"ping-{i}"
        queue.enqueue(
            "app.workers.tasks.cert_ping",
            i,
            job_id=job_id,
            job_timeout=30,
            result_ttl=3600,
        )
    enqueue_s = time.perf_counter() - t0

    done = 0
    deadline = time.time() + max(180, JOBS * 0.04)
    while time.time() < deadline:
        done = int(redis.get("cert:ping:done") or 0)
        if done >= JOBS:
            break
        time.sleep(0.4)
    elapsed = time.perf_counter() - t0
    failed = queue.failed_job_registry.count
    payload = {
        "measured_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "kind": "cert_ping",
        "jobs": JOBS,
        "workers_started": WORKERS,
        "workers_registered": len(workers),
        "enqueue_s": round(enqueue_s, 3),
        "elapsed_s": round(elapsed, 3),
        "throughput_jobs_per_min": round(JOBS / max(elapsed, 0.001) * 60, 1),
        "completed_counter": done,
        "failed_registry": failed,
        "queued_remaining": queue.count,
        "dlq_depth": Queue("analysis_dlq", connection=redis).count,
        "lost": max(0, JOBS - done - failed - queue.count),
        "pass": done >= JOBS and failed == 0 and queue.count == 0,
        "not_run": [n for n in (50000,) if JOBS < n],
    }
    out = ROOT / "ops" / f"cert_queue_ping_{JOBS}.json"
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload, indent=2))
    for proc in procs:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
    return 0 if payload["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
