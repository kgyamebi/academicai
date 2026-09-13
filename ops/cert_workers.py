"""RQ worker scaling. Reuses cert_queue.py with different worker counts. Does not invent 50-worker success."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JOBS = int(os.environ.get("CERT_WORKER_JOBS", "200"))
COUNTS = [int(x) for x in os.environ.get("CERT_WORKER_COUNTS", "1,2,5").split(",") if x.strip()]


def main() -> int:
    runs = {}
    for workers in COUNTS:
        env = os.environ.copy()
        env["CERT_QUEUE_JOBS"] = str(JOBS)
        env["CERT_QUEUE_WORKERS"] = str(workers)
        result_path = ROOT / "ops" / "cert_queue_results.json"
        t0 = time.perf_counter()
        proc = subprocess.run([sys.executable, str(ROOT / "ops" / "cert_queue.py")], env=env)
        elapsed = time.perf_counter() - t0
        payload = {}
        if result_path.exists():
            payload = json.loads(result_path.read_text(encoding="utf-8"))
        runs[str(workers)] = {
            "exit_code": proc.returncode,
            "elapsed_s": round(elapsed, 3),
            "jobs": payload.get("jobs"),
            "statuses": payload.get("statuses"),
            "throughput_jobs_per_min": payload.get("throughput_jobs_per_min"),
            "lost": payload.get("lost"),
            "stuck": payload.get("stuck"),
            "duplicate_ids": payload.get("duplicate_ids"),
            "pass_no_loss_dup_stuck": payload.get("pass_no_loss_dup_stuck"),
        }
    out = {
        "measured_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "jobs_per_run": JOBS,
        "runs": runs,
        "not_run": [n for n in (10, 25, 50) if n not in COUNTS],
        "cpu_memory": "not_sampled_host_metrics",
    }
    dest = ROOT / "ops" / "cert_workers_results.json"
    dest.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(json.dumps(out, indent=2))
    return 0 if all(v.get("pass_no_loss_dup_stuck") for v in runs.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
