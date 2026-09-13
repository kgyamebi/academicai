"""Restore audit: checksums, accidental delete, drop, second restore. Local Docker is not managed Postgres."""

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
    "analysis_findings",
    "payments",
    "credits",
    "subscriptions",
)


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


def counts(engine) -> dict[str, int]:
    with Session(engine) as db:
        out = {}
        for table in TABLES:
            quoted = f'"{table}"' if table == "references" else table
            out[table] = int(db.scalar(text(f"SELECT COUNT(*) FROM {quoted}")) or 0)
        return out


def fingerprints(engine) -> dict[str, str]:
    out = {}
    with Session(engine) as db:
        for table in TABLES:
            quoted = f'"{table}"' if table == "references" else table
            row = db.execute(
                text(
                    f"SELECT COUNT(*)::text, COALESCE(MIN(id::text),''), COALESCE(MAX(id::text),'') FROM {quoted}"
                )
            ).one()
            payload = "|".join(str(x) for x in row)
            out[table] = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]
    return out


def relationship_orphans(engine) -> dict[str, int]:
    """FK orphans after restore. Zero expected. Not a full-row checksum."""
    checks = {
        "documents_missing_user": "SELECT COUNT(*) FROM documents d LEFT JOIN users u ON d.user_id = u.id WHERE u.id IS NULL",
        "assignments_missing_user": "SELECT COUNT(*) FROM assignments a LEFT JOIN users u ON a.user_id = u.id WHERE u.id IS NULL",
        "jobs_missing_assignment": "SELECT COUNT(*) FROM analysis_jobs j LEFT JOIN assignments a ON j.assignment_id = a.id WHERE j.assignment_id IS NOT NULL AND a.id IS NULL",
        "reports_missing_job": "SELECT COUNT(*) FROM analysis_reports r LEFT JOIN analysis_jobs j ON r.job_id = j.id WHERE j.id IS NULL",
        "payments_missing_user": "SELECT COUNT(*) FROM payments p LEFT JOIN users u ON p.user_id = u.id WHERE u.id IS NULL",
        "credits_missing_user": "SELECT COUNT(*) FROM credits c LEFT JOIN users u ON c.user_id = u.id WHERE u.id IS NULL",
        "subscriptions_missing_plan": "SELECT COUNT(*) FROM subscriptions s LEFT JOIN plans p ON s.plan_id = p.id WHERE p.id IS NULL",
    }
    out: dict[str, int] = {}
    with engine.connect() as conn:
        for name, sql in checks.items():
            out[name] = int(conn.execute(text(sql)).scalar() or 0)
    return out


def restore_to(dbname: str) -> float:
    docker("dropdb", "-U", "academiccheck", "--if-exists", "--force", dbname)
    docker("createdb", "-U", "academiccheck", dbname)
    t0 = time.perf_counter()
    docker(
        "pg_restore",
        "-U",
        "academiccheck",
        "-d",
        dbname,
        "--no-owner",
        "/backups/cert.dump",
    )
    return time.perf_counter() - t0


def sql_on(dbname: str, sql: str) -> str:
    result = docker("psql", "-U", "academiccheck", "-d", dbname, "-v", "ON_ERROR_STOP=1", "-c", sql)
    return result.stdout


def main() -> int:
    engine = create_engine(PG, future=True)
    provider = "docker-local"
    if any(token in PG for token in ("amazonaws.com", "neon.tech", "supabase.co", "azure.com", "cloudsql", "rds.")):
        provider = "managed-url-detected"
    before = counts(engine)
    fp_before = fingerprints(engine)

    docker_root("mkdir", "-p", "/backups")
    docker_root("chmod", "777", "/backups")
    t0 = time.perf_counter()
    docker(
        "pg_dump",
        "-U",
        "academiccheck",
        "-d",
        "academiccheck",
        "--format=custom",
        "--file=/backups/cert.dump",
    )
    dump_s = time.perf_counter() - t0

    restore1_s = restore_to("academiccheck_restore")
    restore_url = PG.rsplit("/", 1)[0] + "/academiccheck_restore"
    restore_engine = create_engine(restore_url, future=True)
    after1 = counts(restore_engine)
    fp1 = fingerprints(restore_engine)

    # Accidental deletion on the restore copy, then restore again.
    sql_on("academiccheck_restore", "DELETE FROM assignments WHERE ctid IN (SELECT ctid FROM assignments LIMIT 250);")
    after_delete = counts(restore_engine)
    restore2_s = restore_to("academiccheck_restore")
    restore_engine.dispose()
    restore_engine = create_engine(restore_url, future=True)
    after2 = counts(restore_engine)
    fp2 = fingerprints(restore_engine)

    # Drop findings (corruption / human DROP), restore.
    sql_on("academiccheck_restore", "DROP TABLE IF EXISTS analysis_findings CASCADE;")
    restore3_s = restore_to("academiccheck_restore")
    restore_engine.dispose()
    restore_engine = create_engine(restore_url, future=True)
    after3 = counts(restore_engine)

    # Simulated failed migration then restore.
    migration_error = ""
    try:
        sql_on("academiccheck_restore", "ALTER TABLE users ADD COLUMN definitely_not_a_real_migration_col integer NOT NULL;")
    except subprocess.CalledProcessError as exc:
        migration_error = (exc.stderr or exc.stdout or str(exc))[-400:]
    restore4_s = restore_to("academiccheck_restore")
    restore_engine.dispose()
    restore_engine = create_engine(restore_url, future=True)
    after4 = counts(restore_engine)
    fp4 = fingerprints(restore_engine)

    # Destroy restore environment entirely, recreate.
    docker("dropdb", "-U", "academiccheck", "--if-exists", "--force", "academiccheck_restore")
    restore5_s = restore_to("academiccheck_restore")
    restore_engine.dispose()
    restore_engine = create_engine(restore_url, future=True)
    after5 = counts(restore_engine)
    orphans = relationship_orphans(restore_engine)
    relationships_ok = all(v == 0 for v in orphans.values())

    match = before == after1 == after2 == after3 == after4 == after5
    fp_match = fp_before == fp1 == fp2 == fp4
    payload = {
        "measured_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "provider": provider,
        "managed_postgres": provider != "docker-local",
        "dump_s": round(dump_s, 3),
        "restore_s": {
            "initial": round(restore1_s, 3),
            "after_accidental_delete": round(restore2_s, 3),
            "after_drop_findings": round(restore3_s, 3),
            "after_failed_migration": round(restore4_s, 3),
            "after_destroy_env": round(restore5_s, 3),
        },
        "rto_s": round(restore5_s, 3),
        "rpo": "point-in-time of last pg_dump only; WAL PITR not exercised",
        "before": before,
        "after_initial": after1,
        "after_delete_before_restore": after_delete,
        "after_delete_restore": after2,
        "after_drop_restore": after3,
        "after_migration_restore": after4,
        "after_destroy_restore": after5,
        "fingerprints_before": fp_before,
        "fingerprints_final": fp4,
        "relationship_orphans": orphans,
        "relationships_ok": relationships_ok,
        "counts_match": match,
        "fingerprints_match": fp_match,
        "failed_migration_error_present": bool(migration_error),
        "accidental_delete_reduced_assignments": after_delete.get("assignments", 0) < before.get("assignments", 0),
        "pass": match
        and fp_match
        and relationships_ok
        and before.get("assignments", 0) > 0
        and before.get("analysis_findings", 0) > 0,
    }
    out = ROOT / "ops" / "cert_restore_audit.json"
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(
        json.dumps(
            {
                k: payload[k]
                for k in (
                    "provider",
                    "managed_postgres",
                    "rto_s",
                    "counts_match",
                    "fingerprints_match",
                    "relationships_ok",
                    "pass",
                    "restore_s",
                    "before",
                )
            },
            indent=2,
        )
    )
    engine.dispose()
    restore_engine.dispose()
    return 0 if payload["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
