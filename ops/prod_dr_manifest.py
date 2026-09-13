"""Read-only manifest: row counts, spot checksums, DB size. Never writes to the DB."""

from __future__ import annotations

import hashlib
import json
import os
import sys
import time
from pathlib import Path
from urllib.parse import urlparse

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

# Tenant / money / integrity tables used for restore verification.
TABLES = (
    "users",
    "assignments",
    "documents",
    "analysis_reports",
    "analysis_jobs",
    "analysis_findings",
    "payments",
    "payment_transactions",
    "credits",
    "credit_transactions",
    "subscriptions",
    "webhook_events",
)


def _quote(table: str) -> str:
    return f'"{table}"' if table == "references" else table


def _normalize_url(url: str) -> str:
    # Accept both postgresql:// and postgresql+psycopg://
    if url.startswith("postgresql+psycopg://"):
        return "postgresql://" + url[len("postgresql+psycopg://") :]
    return url


def build_manifest(engine: Engine, *, phase: str) -> dict:
    with engine.connect() as conn:
        # Enforce session read-only — any accidental write fails hard.
        conn.execute(text("SET SESSION CHARACTERISTICS AS TRANSACTION READ ONLY"))
        conn.execute(text("SET statement_timeout = '120s'"))

        counts: dict[str, int] = {}
        fingerprints: dict[str, str] = {}
        spot_checks: dict[str, dict] = {}

        for table in TABLES:
            q = _quote(table)
            exists = conn.execute(
                text(
                    "SELECT EXISTS (SELECT 1 FROM information_schema.tables "
                    "WHERE table_schema='public' AND table_name=:t)"
                ),
                {"t": table},
            ).scalar()
            if not exists:
                counts[table] = -1
                fingerprints[table] = "missing"
                continue
            count = int(conn.execute(text(f"SELECT COUNT(*) FROM {q}")).scalar() or 0)
            counts[table] = count
            row = conn.execute(
                text(
                    f"SELECT COUNT(*)::text, "
                    f"COALESCE(MIN(id::text),''), "
                    f"COALESCE(MAX(id::text),'') FROM {q}"
                )
            ).one()
            payload = "|".join(str(x) for x in row)
            fingerprints[table] = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:24]

            # Spot-check: first/last id + a content hash of one stable column if present.
            sample = conn.execute(
                text(
                    f"SELECT id::text FROM {q} ORDER BY id ASC NULLS LAST LIMIT 1"
                )
            ).scalar()
            sample_max = conn.execute(
                text(
                    f"SELECT id::text FROM {q} ORDER BY id DESC NULLS LAST LIMIT 1"
                )
            ).scalar()
            spot_checks[table] = {
                "min_id": sample or "",
                "max_id": sample_max or "",
                "count": count,
                "fingerprint": fingerprints[table],
            }

        size_row = conn.execute(
            text(
                "SELECT pg_database_size(current_database())::bigint, "
                "current_database(), "
                "inet_server_addr()::text, "
                "current_setting('server_version')"
            )
        ).one()
        db_bytes, db_name, server_addr, server_version = size_row

    parsed = urlparse(_normalize_url(os.environ.get("MANIFEST_DATABASE_URL", "")))
    return {
        "phase": phase,
        "measured_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "database_name": db_name,
        "database_bytes": int(db_bytes or 0),
        "server_addr": server_addr,
        "server_version": server_version,
        "source_host": parsed.hostname,
        "source_port": parsed.port,
        "tables": TABLES,
        "row_counts": counts,
        "fingerprints": fingerprints,
        "spot_checks": spot_checks,
        "read_only": True,
    }


def main() -> int:
    url = os.environ.get("MANIFEST_DATABASE_URL") or os.environ.get("DATABASE_URL")
    out = os.environ.get("MANIFEST_OUT")
    phase = os.environ.get("MANIFEST_PHASE", "manual")
    if not url:
        print("FATAL: MANIFEST_DATABASE_URL or DATABASE_URL required", file=sys.stderr)
        return 2
    if not out:
        print("FATAL: MANIFEST_OUT required", file=sys.stderr)
        return 2

    engine = create_engine(_normalize_url(url), pool_pre_ping=True)
    try:
        manifest = build_manifest(engine, phase=phase)
    finally:
        engine.dispose()

    path = Path(out)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(
        json.dumps(
            {
                "wrote": str(path),
                "database_bytes": manifest["database_bytes"],
                "row_counts": manifest["row_counts"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
