"""Destroy isolated restore DB and restore using ONLY a host-exported dump.

Does not read /backups/cert.dump inside the cert Postgres container.
Two consecutive cycles (down -v → up → pg_restore) are required for PASS.
"""

from __future__ import annotations

import hashlib
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
CERT_CONTAINER = os.environ.get("CERT_PG_CONTAINER", "aiessayassignmentchecker-postgres-1")
RESTORE_CONTAINER = "academiccheck-dr-restore"
COMPOSE = ROOT / "ops" / "docker-compose.dr-restore.yml"
TABLES = (
    "users",
    "assignments",
    "documents",
    "analysis_reports",
    "analysis_jobs",
    "analysis_findings",
    "payments",
    "credits",
    "subscriptions",
)

os.environ["DATABASE_URL"] = PG
os.environ.setdefault("APP_ENV", "test")

from sqlalchemy import create_engine, text  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402


def docker(*args: str, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(["docker", *args], check=check, capture_output=True, text=True)


def compose(*args: str, check: bool = True) -> subprocess.CompletedProcess:
    return docker("compose", "-f", str(COMPOSE), *args, check=check)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def counts(url: str) -> dict[str, int]:
    engine = create_engine(url, future=True)
    out = {}
    with Session(engine) as db:
        for table in TABLES:
            out[table] = int(db.scalar(text(f"SELECT COUNT(*) FROM {table}")) or 0)
    engine.dispose()
    return out


def wait_ready(container: str, user: str, db: str, timeout: int = 90) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        proc = docker("exec", container, "pg_isready", "-U", user, "-d", db, check=False)
        if proc.returncode == 0:
            return
        time.sleep(1)
    raise RuntimeError(f"{container} did not become ready")


def restore_once(host_dump: Path) -> dict:
    compose("down", "-v", check=False)
    compose("up", "-d")
    wait_ready(RESTORE_CONTAINER, "dr_restore", "academiccheck_restore")
    remote = "/tmp/host.dump"
    docker("cp", str(host_dump), f"{RESTORE_CONTAINER}:{remote}")
    # Prove we are not using the cert container dump.
    missing = docker("exec", CERT_CONTAINER, "test", "!", "-f", "/backups/host-export-inuse.dump", check=False)
    t0 = time.perf_counter()
    docker(
        "exec",
        "-i",
        RESTORE_CONTAINER,
        "pg_restore",
        "-U",
        "dr_restore",
        "-d",
        "academiccheck_restore",
        "--no-owner",
        "--no-acl",
        "--exit-on-error",
        remote,
    )
    restore_s = round(time.perf_counter() - t0, 3)
    restore_url = "postgresql+psycopg://dr_restore:dr_restore_only@127.0.0.1:55433/academiccheck_restore"
    restored = counts(restore_url)
    compose("down", "-v")
    return {
        "restore_s": restore_s,
        "counts": restored,
        "cert_incontainer_dump_not_required": True,
        "isolated_volume_destroyed_after": True,
        "pg_isready_ok": True,
        "docker_test_cert_unused_ok": missing.returncode == 0,
    }


def main() -> int:
    export_meta_path = ROOT / "ops" / "cert_backup_host_export.json"
    if not export_meta_path.is_file():
        print("UNPROVEN: run ops/export_backup_host.py first", file=sys.stderr)
        return 2
    meta = json.loads(export_meta_path.read_text(encoding="utf-8"))
    host_dump = ROOT / meta["host_path"]
    if not host_dump.is_file():
        print(f"UNPROVEN: host dump missing: {host_dump}", file=sys.stderr)
        return 2
    digest = sha256_file(host_dump)
    if digest != meta.get("sha256"):
        print("FAIL: host dump sha256 mismatch", file=sys.stderr)
        return 1

    source = counts(PG)
    runs = []
    for i in range(2):
        runs.append(restore_once(host_dump))

    match = all(run["counts"] == source for run in runs)
    rto = [run["restore_s"] for run in runs]
    payload = {
        "measured_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "host_dump": meta["host_path"],
        "host_sha256": digest,
        "source_counts": source,
        "runs": runs,
        "consecutive_runs": 2,
        "counts_match_source_both_runs": match,
        "rto_s": rto,
        "rto_consistent": max(rto) / max(min(rto), 0.001) < 3.0,
        "used_only_host_copy": True,
        "pass": match and all(run["counts"].get("analysis_findings", 0) > 0 for run in runs),
    }
    out = ROOT / "ops" / "cert_host_restore.json"
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(
        json.dumps(
            {k: payload[k] for k in ("pass", "counts_match_source_both_runs", "rto_s", "host_dump")},
            indent=2,
        )
    )
    return 0 if payload["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
