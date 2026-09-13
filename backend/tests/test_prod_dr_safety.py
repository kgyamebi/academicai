"""Safety contract tests for prod DR guards (no production credentials; no bash required)."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
GUARDS = ROOT / "ops" / "prod_dr_guards.py"


def _load():
    spec = importlib.util.spec_from_file_location("prod_dr_guards", GUARDS)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)
    return mod


def test_backup_refuses_localhost():
    g = _load()
    with pytest.raises(SystemExit) as ei:
        g.guard_backup_url("postgresql://u:p@127.0.0.1:5432/academiccheck")
    assert "REFUSED" in str(ei.value)


def test_backup_allows_localhost_with_override():
    g = _load()
    g.guard_backup_url("postgresql://u:p@127.0.0.1:5432/academiccheck", allow_nonprod=True)


def test_restore_refuses_without_confirmation():
    g = _load()
    with pytest.raises(SystemExit):
        g.guard_restore_url(
            "postgresql://dr_restore:x@127.0.0.1:55433/academiccheck_restore",
            confirm="",
        )


def test_restore_refuses_prod_looking_host():
    g = _load()
    with pytest.raises(SystemExit) as ei:
        g.guard_restore_url(
            "postgresql://u:p@mydb.abc123.rds.amazonaws.com:5432/academiccheck",
            confirm=g.CONFIRM_TOKEN,
            allow_nonlocal_isolated=True,
        )
    assert "refuse" in str(ei.value).lower()


def test_restore_refuses_when_url_equals_prod():
    g = _load()
    url = "postgresql://u:p@127.0.0.1:55433/academiccheck_restore"
    with pytest.raises(SystemExit) as ei:
        g.guard_restore_url(url, confirm=g.CONFIRM_TOKEN, prod_url=url)
    assert "equals" in str(ei.value).lower()


def test_restore_allows_isolated_localhost():
    g = _load()
    g.guard_restore_url(
        "postgresql://dr_restore:x@127.0.0.1:55433/academiccheck_restore",
        confirm=g.CONFIRM_TOKEN,
        prod_url="postgresql://u:p@prod.example.com:5432/academiccheck",
    )


def test_verify_cli_refuses_prod_url(tmp_path):
    manifest = tmp_path / "m.json"
    manifest.write_text('{"row_counts":{},"fingerprints":{},"spot_checks":{}}', encoding="utf-8")
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "ops" / "prod_dr_verify.py"),
            "--manifest",
            str(manifest),
            "--database-url",
            "postgresql://u:p@db.xxx.rds.amazonaws.com:5432/academiccheck",
        ],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
    )
    assert result.returncode == 3


def test_guards_cli_backup_exit_code():
    import os

    env = os.environ.copy()
    env["PROD_DATABASE_URL"] = "postgresql://u:p@127.0.0.1:5432/db"
    env.pop("ALLOW_NONPROD_BACKUP", None)
    result = subprocess.run(
        [sys.executable, str(GUARDS), "backup"],
        env=env,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 3
    assert "REFUSED" in (result.stderr + result.stdout)
