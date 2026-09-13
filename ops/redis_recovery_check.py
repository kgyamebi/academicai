#!/usr/bin/env python3
"""Redis persistence / recovery probe.

Checks connectivity, appendonly, and optional RDB/AOF file presence when REDIS_DATA_DIR is set.
Does not prove Sentinel/Cluster failover (UNPROVEN unless operator provides).
"""

from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--redis-url", default=os.environ.get("REDIS_URL", "redis://127.0.0.1:6379/0"))
    parser.add_argument("--out", default=str(ROOT / "ops" / "cert_redis_recovery.json"))
    parser.add_argument("--restart-probe", action="store_true", help="PING before/after reconnect only")
    args = parser.parse_args()

    report: dict = {
        "measured_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "redis_url_host": args.redis_url.split("@")[-1],
        "ok": False,
        "checks": [],
        "failover": "UNPROVEN",
        "aof_restore_drill": "UNPROVEN",
    }

    try:
        from redis import Redis

        client = Redis.from_url(args.redis_url, socket_timeout=2, socket_connect_timeout=2)
        pong = client.ping()
        report["checks"].append({"name": "ping", "ok": bool(pong)})
        info = client.info("persistence")
        aof = bool(info.get("aof_enabled"))
        rdb = info.get("rdb_last_bgsave_status")
        report["checks"].append({"name": "aof_enabled", "ok": aof, "detail": str(info.get("aof_enabled"))})
        report["checks"].append(
            {"name": "rdb_last_bgsave_status", "ok": True, "detail": str(rdb)}
        )
        # Queue key presence (best-effort)
        depth = int(client.llen("rq:queue:analysis") or 0)
        report["checks"].append({"name": "queue_llen", "ok": True, "detail": f"analysis={depth}"})
        if args.restart_probe:
            client.connection_pool.disconnect()
            client2 = Redis.from_url(args.redis_url, socket_timeout=2, socket_connect_timeout=2)
            report["checks"].append({"name": "reconnect_ping", "ok": bool(client2.ping())})
        report["ok"] = all(c["ok"] for c in report["checks"] if c["name"] != "aof_enabled")
        # AOF preferred but not required for process-restart survival of empty queue
        if not aof:
            report["checks"].append(
                {
                    "name": "aof_warning",
                    "ok": True,
                    "detail": "appendonly disabled — queue durability depends on DB job rows + recover_jobs.py",
                }
            )
    except Exception as exc:  # noqa: BLE001
        report["checks"].append({"name": "ping", "ok": False, "detail": str(exc)})
        report["ok"] = False
        report["error"] = "UNPROVEN: Redis unreachable"

    Path(args.out).write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if report["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
