#!/usr/bin/env python3
"""Run engineerable DR drills that do not require Docker/managed cloud."""

from __future__ import annotations

import gzip
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "ops" / "cert_dr_local_drill.json"


def main() -> int:
    py = sys.executable
    results: dict = {
        "measured_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "docker_required_drills": "NOT_RUN (daemon unavailable or not invoked)",
        "managed_pitr": False,
        "multi_region": False,
        "production_dr_certified": False,
        "drills": {},
    }

    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        plain = td_path / "sample.sql.gz"
        with gzip.open(plain, "wb") as fh:
            fh.write(b"-- AcademicCheck DR sample dump\nSELECT 1;\n" + b"x" * 4096)
        enc = td_path / "sample.sql.gz.enc"
        key = "dr-local-drill-encryption-key-32b"
        sys.path.insert(0, str(ROOT / "ops"))
        from backup_crypto import decrypt_file, encrypt_file

        encrypt_file(plain, enc, key)
        dec = td_path / "sample.sql.gz.out"
        decrypt_file(enc, dec, key)
        roundtrip_ok = plain.read_bytes() == dec.read_bytes()
        env = {**os.environ, "BACKUP_ENCRYPTION_KEY": key}
        verify = subprocess.run(
            [
                py,
                str(ROOT / "ops" / "backup_verification.py"),
                "--backup",
                str(enc),
                "--out",
                str(ROOT / "ops" / "cert_backup_verification.json"),
            ],
            env=env,
            capture_output=True,
            text=True,
        )
        results["drills"]["encrypted_backup_roundtrip"] = {
            "ok": roundtrip_ok and verify.returncode == 0,
            "roundtrip_bytes_match": roundtrip_ok,
            "verification_exit": verify.returncode,
        }

    storage = subprocess.run(
        [
            py,
            str(ROOT / "ops" / "verify_storage.py"),
            "--storage-root",
            str(ROOT / "backups" / "dr-storage-fixture"),
            "--out",
            str(ROOT / "ops" / "cert_storage_recovery.json"),
        ],
        capture_output=True,
        text=True,
    )
    results["drills"]["storage_local_recovery"] = {
        "ok": storage.returncode == 0,
        "exit": storage.returncode,
        "artifact": "ops/cert_storage_recovery.json",
    }

    redis = subprocess.run(
        [
            py,
            str(ROOT / "ops" / "redis_recovery_check.py"),
            "--out",
            str(ROOT / "ops" / "cert_redis_recovery.json"),
        ],
        capture_output=True,
        text=True,
    )
    results["drills"]["redis_probe"] = {
        "ok": redis.returncode == 0,
        "exit": redis.returncode,
        "optional": True,
        "note": "Process probe only; AOF restore / Sentinel UNPROVEN",
    }

    pytest_proc = subprocess.run(
        [
            py,
            "-m",
            "pytest",
            "-q",
            "tests/test_prod_dr_safety.py",
            "tests/test_dr_automation.py",
            "tests/test_mfa_and_recovery.py::test_recover_orphaned_job_exactly_once",
            "--tb=line",
        ],
        cwd=str(ROOT / "backend"),
        env={
            **os.environ,
            "APP_ENV": "test",
            "DATABASE_URL": "sqlite:///./dr_drill.db",
            "JWT_SECRET_KEY": "ci-jwt-secret-key-32-bytes-minimum",
            "APP_SECRET_KEY": "ci-secret",
        },
        capture_output=True,
        text=True,
    )
    results["drills"]["automation_pytest"] = {
        "ok": pytest_proc.returncode == 0,
        "exit": pytest_proc.returncode,
        "stdout_tail": (pytest_proc.stdout or "")[-2000:],
    }

    audit = ROOT / "ops" / "cert_restore_audit.json"
    results["drills"]["historical_postgres_restore_audit"] = {
        "ok": audit.is_file(),
        "path": "ops/cert_restore_audit.json",
        "note": "Prior local Docker evidence (2026-09-07). Not re-executed this run.",
    }

    required = [
        results["drills"]["encrypted_backup_roundtrip"],
        results["drills"]["storage_local_recovery"],
        results["drills"]["automation_pytest"],
        results["drills"]["historical_postgres_restore_audit"],
    ]
    results["ok_local_package"] = all(d.get("ok") for d in required)
    results["redis_optional_ok"] = bool(results["drills"]["redis_probe"].get("ok"))
    results["launch_recommendation"] = (
        "NO-GO — production DR not certified (managed PITR, offsite schedule, "
        "multi-region, live prod dump/restore, S3 replication still open)"
    )

    OUT.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(json.dumps({"ok_local_package": results["ok_local_package"], "out": str(OUT)}, indent=2))
    return 0 if results["ok_local_package"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
