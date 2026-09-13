"""Backup, drop, restore drill against the certification Postgres container."""

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

PG = os.environ.get(
    "CERT_DATABASE_URL",
    "postgresql+psycopg://academiccheck:academiccheck@127.0.0.1:55432/academiccheck",
)
CONTAINER = os.environ.get("CERT_PG_CONTAINER", "aiessayassignmentchecker-postgres-1")
os.environ["DATABASE_URL"] = PG
os.environ.setdefault("APP_ENV", "test")

from sqlalchemy import create_engine, text  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402


TABLES = (
    "users",
    "assignments",
    "documents",
    "analysis_reports",
    "analysis_jobs",
    "payments",
    "credits",
    "subscriptions",
)


def counts(engine) -> dict[str, int]:
    with Session(engine) as db:
        out = {}
        for table in TABLES:
            out[table] = int(db.scalar(text(f"SELECT COUNT(*) FROM {table}")) or 0)
        return out


def docker(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["docker", "exec", "-i", CONTAINER, *args],
        check=True,
        capture_output=True,
        text=True,
    )


def docker_root(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["docker", "exec", "-u", "root", "-i", CONTAINER, *args],
        check=True,
        capture_output=True,
        text=True,
    )


def main() -> int:
    engine = create_engine(PG, future=True)
    before = counts(engine)
    docker_root("mkdir", "-p", "/backups")
    docker_root("chmod", "777", "/backups")
    t0 = time.perf_counter()
    dump = docker(
        "pg_dump",
        "-U",
        "academiccheck",
        "-d",
        "academiccheck",
        "--format=custom",
        "--file=/backups/cert.dump",
    )
    dump_s = time.perf_counter() - t0
    docker("dropdb", "-U", "academiccheck", "--if-exists", "academiccheck_restore")
    docker("createdb", "-U", "academiccheck", "academiccheck_restore")
    t1 = time.perf_counter()
    docker(
        "pg_restore",
        "-U",
        "academiccheck",
        "-d",
        "academiccheck_restore",
        "--no-owner",
        "/backups/cert.dump",
    )
    restore_s = time.perf_counter() - t1
    restore_url = PG.rsplit("/", 1)[0] + "/academiccheck_restore"
    restore_engine = create_engine(restore_url, future=True)
    after = counts(restore_engine)
    match = before == after
    payload = {
        "measured_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "dump_s": round(dump_s, 3),
        "restore_s": round(restore_s, 3),
        "before": before,
        "after": after,
        "counts_match": match,
        "pass": match and after.get("assignments", 0) > 0,
        "stderr_dump": (dump.stderr or "")[-500:],
    }
    out = ROOT / "ops" / "cert_restore_results.json"
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload, indent=2))
    engine.dispose()
    restore_engine.dispose()
    return 0 if payload["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
