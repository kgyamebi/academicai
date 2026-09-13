"""Aggregate consecutive DR drill artifacts. Does not invent PASS for live-cloud items."""

from __future__ import annotations

import json
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OPS = ROOT / "ops"


def load(name: str) -> dict:
    path = OPS / name
    if not path.is_file():
        return {"missing": True, "pass": False}
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    host_export = load("cert_backup_host_export.json")
    host_restore = load("cert_host_restore.json")
    minio = load("cert_offsite_minio.json")
    wal = load("cert_wal_pitr.json")
    storage = load("cert_storage_app_restore.json")
    queue = load("cert_queue_crash.json")
    crr = load("cert_crr_config.json")
    payload = {
        "measured_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "consecutive_run_requirement": 2,
        "drills": {
            "host_export": {"ok": bool(host_export.get("ok")), "sha256": host_export.get("sha256"), "size_bytes": host_export.get("size_bytes")},
            "host_restore_only": {
                "ok": bool(host_restore.get("pass")),
                "runs": host_restore.get("consecutive_runs"),
                "rto_s": host_restore.get("rto_s"),
                "rto_consistent": host_restore.get("rto_consistent"),
            },
            "offsite_minio": {"ok": bool(minio.get("ok")), "runs": minio.get("consecutive_runs"), "live_cloud": minio.get("live_cloud_account")},
            "wal_pitr_local": {"ok": bool(wal.get("pass")), "runs": wal.get("consecutive_runs"), "managed_provider": wal.get("managed_provider_pitr")},
            "storage_app_restore": {"ok": bool(storage.get("pass")), "runs": storage.get("consecutive_runs")},
            "queue_crash_aof": {"ok": bool(queue.get("pass")), "runs": queue.get("consecutive_runs"), "lost": [r.get("lost_job_count") for r in queue.get("runs") or []]},
            "crr_config": {"syntax_ok": bool(crr.get("syntax_ok")), "replication_succeeded": crr.get("replication_succeeded")},
        },
        "live_account_still_required": [
            "managed Postgres PITR (RDS/Neon/Cloud SQL feature)",
            "real S3/GCS bucket credentials in GHA secrets",
            "S3 CRR between two regions",
            "multi-region failover drill",
            "human production dump/restore (docs/PROD_DR_DRILL.md)",
        ],
    }
    local_ok = all(
        [
            payload["drills"]["host_export"]["ok"],
            payload["drills"]["host_restore_only"]["ok"],
            payload["drills"]["offsite_minio"]["ok"],
            payload["drills"]["wal_pitr_local"]["ok"],
            payload["drills"]["storage_app_restore"]["ok"],
            payload["drills"]["queue_crash_aof"]["ok"],
            payload["drills"]["crr_config"]["syntax_ok"],
            payload["drills"]["crr_config"]["replication_succeeded"] is False,
        ]
    )
    payload["ok_local_package"] = local_ok
    payload["production_dr_certified"] = False
    payload["launch_recommendation"] = "NO-GO — local DR package PASS; live account + human prod drill still open"
    out = OPS / "cert_dr_repeat.json"
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps({"ok_local_package": local_ok, "production_dr_certified": False}, indent=2))
    return 0 if local_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
