"""10 / 25 / 50 RQ workers × 5k then 10k REAL analysis jobs. No invented PASS."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COUNTS = [int(x) for x in os.environ.get("CERT_WORKER_COUNTS", "10,25,50").split(",") if x.strip()]
JOB_TIERS = [int(x) for x in os.environ.get("CERT_WORKER_JOB_TIERS", "5000,10000").split(",") if x.strip()]


def main() -> int:
    runs = {}
    not_reached = []
    for jobs in JOB_TIERS:
        for workers in COUNTS:
            key = f"workers_{workers}_jobs_{jobs}"
            env = os.environ.copy()
            env["CERT_QUEUE_JOBS"] = str(jobs)
            env["CERT_QUEUE_WORKERS"] = str(workers)
            env.setdefault(
                "CERT_DATABASE_URL",
                "postgresql+psycopg://academiccheck:academiccheck@127.0.0.1:56432/academiccheck",
            )
            env.setdefault("CERT_REDIS_URL", "redis://127.0.0.1:56380/0")
            print(f"=== {key} ===", flush=True)
            t0 = time.perf_counter()
            proc = subprocess.run([sys.executable, str(ROOT / "ops" / "cert_queue.py")], env=env)
            elapsed = time.perf_counter() - t0
            result_path = ROOT / "ops" / "cert_queue_results.json"
            payload = {}
            if result_path.exists():
                payload = json.loads(result_path.read_text(encoding="utf-8"))
            entry = {
                "exit_code": proc.returncode,
                "elapsed_s": round(elapsed, 3),
                "jobs": payload.get("jobs"),
                "workers_started": payload.get("workers_started"),
                "workers_registered": payload.get("workers_registered"),
                "statuses": payload.get("statuses"),
                "throughput_jobs_per_min": payload.get("throughput_jobs_per_min"),
                "lost": payload.get("lost"),
                "stuck": payload.get("stuck"),
                "duplicate_ids": payload.get("duplicate_ids"),
                "pass_no_loss_dup_stuck": payload.get("pass_no_loss_dup_stuck"),
            }
            runs[key] = entry
            if proc.returncode != 0 and not payload.get("pass_no_loss_dup_stuck"):
                not_reached.append({"cell": key, "reason": "run_failed_or_jobs_not_clean"})
    out = {
        "measured_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "runs": runs,
        "not_reached": not_reached,
        "cpu_memory": "host_rss_not_sampled",
    }
    dest = ROOT / "ops" / "cert_worker_scale.json"
    dest.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(json.dumps({"keys": list(runs), "not_reached": not_reached}, indent=2))
    return 0 if not not_reached else 1


if __name__ == "__main__":
    raise SystemExit(main())
