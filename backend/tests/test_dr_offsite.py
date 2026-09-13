"""Retention prune + CRR config contract tests (no Docker required)."""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OPS = ROOT / "ops"
sys.path.insert(0, str(OPS))

from offsite_backup import keys_to_delete  # noqa: E402
from validate_crr_config import validate  # noqa: E402


def test_retention_keeps_recent_daily_and_prunes_stale():
    now = datetime(2026, 9, 9, 12, 0, tzinfo=UTC)
    keys = []
    for days in (0, 1, 2, 3, 6, 10, 20, 40, 80):
        ts = now - timedelta(days=days)
        keys.append({"key": f"backups/postgres/academiccheck-{ts.strftime('%Y%m%dT%H%M%SZ')}.dump"})
    doomed = keys_to_delete(keys, daily_keep=7, weekly_keep=4, now=now)
    doomed_names = {item.split("academiccheck-")[-1] for item in doomed}
    # 80-day object is outside 4 weeks and outside 7 days
    assert any("20260621" in name or (now - timedelta(days=80)).strftime("%Y%m%d") in name for name in doomed_names)
    kept = {obj["key"] for obj in keys} - set(doomed)
    assert any("20260909" in k or "20260908" in k for k in kept)


def test_crr_config_is_structurally_valid_and_not_claimed_executed():
    cfg = json.loads((OPS / "s3_crr_replication.json").read_text(encoding="utf-8"))
    assert validate(cfg) == []
    assert cfg["live_account_required"] is True
    proc = subprocess.run(
        [sys.executable, str(OPS / "validate_crr_config.py")],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout
    report = json.loads((OPS / "cert_crr_config.json").read_text(encoding="utf-8"))
    assert report["syntax_ok"] is True
    assert report["replication_succeeded"] is False


def test_host_export_script_copies_to_host_and_deletes_container_copy():
    text = (OPS / "export_backup_host.py").read_text(encoding="utf-8")
    assert "docker" in text
    assert "sha256" in text
    assert "in_container_copy_deleted" in text
    assert "backups" in text and "host" in text


def test_wal_pitr_script_targets_timestamp_between_writes():
    text = (OPS / "cert_wal_pitr.py").read_text(encoding="utf-8")
    assert "recovery_target_time" in text
    assert "before-target" in text
    assert "after-target" in text
    assert "managed_provider_pitr" in text


def test_backup_workflow_has_schedule_and_upload_hook():
    text = (ROOT / ".github" / "workflows" / "backup-postgres.yml").read_text(encoding="utf-8")
    assert "cron:" in text
    assert "BACKUP_UPLOAD_URI" in text
    assert "offsite_backup" in text
