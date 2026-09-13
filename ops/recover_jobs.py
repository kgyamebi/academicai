#!/usr/bin/env python3
"""Recover orphaned / stale analysis jobs from Postgres (queue durability layer).

Uses the same recover_orphaned_jobs / reap_stale_jobs paths as the worker.
Does not resurrect RQ payloads lost with Redis volume destruction.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--database-url", default=os.environ.get("DATABASE_URL", ""))
    parser.add_argument("--out", default=str(ROOT / "ops" / "cert_job_recovery.json"))
    parser.add_argument("--orphan-seconds", type=int, default=90)
    parser.add_argument("--stale-seconds", type=int, default=900)
    args = parser.parse_args()

    if not args.database_url:
        report = {"ok": False, "error": "UNPROVEN: DATABASE_URL not set"}
        Path(args.out).write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(json.dumps(report, indent=2))
        return 2

    os.environ["DATABASE_URL"] = args.database_url
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session

    from app.services.analysis.runner import recover_orphaned_jobs, reap_stale_jobs

    engine = create_engine(args.database_url, pool_pre_ping=True)
    with Session(engine) as db:
        recovered = [str(x) for x in recover_orphaned_jobs(db, older_than_seconds=args.orphan_seconds)]
        reaped = reap_stale_jobs(db, older_than_seconds=args.stale_seconds)
        db.commit()
    engine.dispose()

    report = {
        "ok": True,
        "recovered_orphans": recovered,
        "recovered_count": len(recovered),
        "reaped_stale": reaped,
        "note": "DB job rows only; Redis RQ payloads are not restored by this script.",
    }
    Path(args.out).write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
