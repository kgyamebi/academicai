"""DR automation contract tests — no Docker, no production credentials."""

from __future__ import annotations

import gzip
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OPS = ROOT / "ops"


def test_backup_crypto_roundtrip(tmp_path):
    sys.path.insert(0, str(OPS))
    from backup_crypto import decrypt_file, encrypt_file

    plain = tmp_path / "a.sql.gz"
    with gzip.open(plain, "wb") as fh:
        fh.write(b"SELECT 1;\n" + b"z" * 2048)
    enc = tmp_path / "a.sql.gz.enc"
    out = tmp_path / "a.sql.gz.out"
    encrypt_file(plain, enc, "test-backup-key-material")
    decrypt_file(enc, out, "test-backup-key-material")
    assert plain.read_bytes() == out.read_bytes()


def test_backup_verification_gzip(tmp_path):
    plain = tmp_path / "b.sql.gz"
    with gzip.open(plain, "wb") as fh:
        fh.write(b"-- dump\n")
    out = tmp_path / "verify.json"
    proc = subprocess.run(
        [sys.executable, str(OPS / "backup_verification.py"), "--backup", str(plain), "--out", str(out)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout
    report = json.loads(out.read_text(encoding="utf-8"))
    assert report["ok"] is True


def test_verify_storage_delete_corrupt_restore(tmp_path):
    storage = tmp_path / "store"
    out = tmp_path / "storage.json"
    proc = subprocess.run(
        [
            sys.executable,
            str(OPS / "verify_storage.py"),
            "--storage-root",
            str(storage),
            "--out",
            str(out),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    report = json.loads(out.read_text(encoding="utf-8"))
    assert report["ok"] is True
    assert report["s3_replication"] is False


def test_restore_database_script_mentions_guards():
    text = (OPS / "restore_database.sh").read_text(encoding="utf-8")
    assert "prod_dr_guards.py" in text
    assert "restore_postgres.sh" in text


def test_recover_jobs_refuses_without_database_url(tmp_path):
    out = tmp_path / "jobs.json"
    env = {k: v for k, v in os.environ.items() if k != "DATABASE_URL"}
    proc = subprocess.run(
        [sys.executable, str(OPS / "recover_jobs.py"), "--out", str(out)],
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )
    assert proc.returncode == 2
    assert json.loads(out.read_text(encoding="utf-8"))["ok"] is False


def test_restore_audit_includes_relationship_checks():
    text = (OPS / "cert_restore_audit.py").read_text(encoding="utf-8")
    assert "relationship_orphans" in text
    assert "documents_missing_user" in text
    assert "relationships_ok" in text


def test_host_restore_uses_isolated_compose_not_cert_volume():
    text = (OPS / "cert_host_restore.py").read_text(encoding="utf-8")
    assert "docker-compose.dr-restore.yml" in text
    assert "used_only_host_copy" in text
    assert "consecutive_runs" in text
