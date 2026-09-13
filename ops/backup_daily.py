#!/usr/bin/env python3
"""Daily Postgres backup for set-and-forget ops (Windows-friendly).

Uses pg_dump when available. Writes timestamped .sql.gz under ops/backups/.
Alerts via ALERT_SINK_FILE on failure.

  python ops/backup_daily.py
"""

from __future__ import annotations

import gzip
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "ops" / "backups"
SINK = Path(os.environ.get("ALERT_SINK_FILE") or (ROOT / "ops" / "evidence" / "alerts.jsonl"))


def alert(title: str, detail: str) -> None:
    import json

    SINK.parent.mkdir(parents=True, exist_ok=True)
    row = {
        "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source": "backup_daily",
        "severity": "critical",
        "title": title,
        "detail": detail,
    }
    with SINK.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row) + "\n")
    print(title, detail, file=sys.stderr)


def main() -> int:
    url = os.environ.get("DATABASE_URL") or ""
    if not url:
        env_path = ROOT / "backend" / ".env"
        if env_path.exists():
            for line in env_path.read_text(encoding="utf-8").splitlines():
                if line.startswith("DATABASE_URL="):
                    url = line.split("=", 1)[1].strip()
                    break
    if not url or url.startswith("sqlite"):
        alert("backup_skipped", "No Postgres DATABASE_URL")
        return 1
    # postgresql+psycopg://user:pass@host:5432/db
    cleaned = url.replace("postgresql+psycopg://", "postgresql://").replace("postgresql+psycopg2://", "postgresql://")
    parsed = urlparse(cleaned)
    if not shutil.which("pg_dump"):
        alert("backup_failed", "pg_dump not found on PATH")
        return 1
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    raw = OUT_DIR / f"academiccheck_{stamp}.sql"
    env = os.environ.copy()
    if parsed.password:
        env["PGPASSWORD"] = parsed.password
    cmd = [
        "pg_dump",
        "-h",
        parsed.hostname or "127.0.0.1",
        "-p",
        str(parsed.port or 5432),
        "-U",
        parsed.username or "academiccheck",
        "-d",
        (parsed.path or "/academiccheck").lstrip("/") or "academiccheck",
        "-f",
        str(raw),
    ]
    proc = subprocess.run(cmd, env=env, capture_output=True, text=True)
    if proc.returncode != 0:
        alert("backup_failed", proc.stderr[-500:] or "pg_dump failed")
        return 1
    gz = Path(str(raw) + ".gz")
    with raw.open("rb") as src, gzip.open(gz, "wb") as dst:
        shutil.copyfileobj(src, dst)
    raw.unlink(missing_ok=True)
    # Retain 14 days
    for old in sorted(OUT_DIR.glob("academiccheck_*.sql.gz"))[:-14]:
        old.unlink(missing_ok=True)
    print(f"backup ok {gz}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
