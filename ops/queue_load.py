"""Enqueue N analysis jobs only when Redis and workers are already running.

This is a staging harness, not a CI fake. It refuses to invent success.
"""

from __future__ import annotations

import argparse
import sys
import time

from redis import Redis
from rq import Queue, Worker


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--jobs", type=int, default=100)
    parser.add_argument("--redis", default="redis://127.0.0.1:6379/0")
    args = parser.parse_args()
    client = Redis.from_url(args.redis, socket_timeout=2)
    try:
        client.ping()
    except Exception as exc:  # noqa: BLE001
        print(f"UNPROVEN: Redis unreachable ({exc})")
        return 2
    workers = Worker.all(connection=client)
    if not workers:
        print("UNPROVEN: no RQ workers registered")
        return 2
    queue = Queue("analysis", connection=client)
    started = time.time()
    for index in range(args.jobs):
        queue.enqueue("app.workers.tasks.run_analysis_job", f"load-{index}", job_timeout=600)
    print(f"enqueued={args.jobs} workers={len(workers)} queued={queue.count} elapsed_s={time.time() - started:.2f}")
    print("Watch the queue until finished. Lost/duplicate proof requires job ids from a real analysis run.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
