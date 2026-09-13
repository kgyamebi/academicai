"""EXPLAIN ANALYZE + keyset vs deep OFFSET on the cert Postgres. No row inserts."""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

PG = os.environ.get(
    "CERT_DATABASE_URL",
    "postgresql+psycopg://academiccheck:academiccheck@127.0.0.1:55432/academiccheck",
)

from sqlalchemy import create_engine, text  # noqa: E402


def pct(samples: list[float], p: float) -> float:
    ordered = sorted(samples)
    return ordered[min(len(samples) - 1, int((len(samples) - 1) * p / 100))]


def timed(engine, sql: str, params: dict, loops: int = 12) -> dict:
    samples = []
    with engine.connect() as conn:
        for _ in range(loops):
            start = time.perf_counter()
            conn.execute(text(sql), params).fetchall()
            samples.append((time.perf_counter() - start) * 1000)
    return {
        "n": loops,
        "p50_ms": round(pct(samples, 50), 3),
        "p95_ms": round(pct(samples, 95), 3),
        "p99_ms": round(pct(samples, 99), 3),
        "max_ms": round(max(samples), 3),
    }


def explain(engine, sql: str, params: dict) -> str:
    with engine.connect() as conn:
        plan = conn.execute(text("EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT) " + sql), params)
        return "\n".join(row[0] for row in plan)


def ensure_keyset_indexes(engine) -> list[str]:
    created = []
    statements = [
        (
            "ix_assignments_user_updated_id",
            "CREATE INDEX IF NOT EXISTS ix_assignments_user_updated_id "
            "ON assignments (user_id, updated_at, id) WHERE deleted_at IS NULL",
        ),
        (
            "ix_analysis_findings_report_created_id",
            "CREATE INDEX IF NOT EXISTS ix_analysis_findings_report_created_id "
            "ON analysis_findings (report_id, created_at, id)",
        ),
        (
            "ix_documents_user_created_id",
            "CREATE INDEX IF NOT EXISTS ix_documents_user_created_id "
            "ON documents (user_id, created_at, id) WHERE deleted_at IS NULL",
        ),
    ]
    with engine.begin() as conn:
        for name, sql in statements:
            conn.execute(text(sql))
            created.append(name)
        conn.execute(text("ANALYZE assignments"))
        conn.execute(text("ANALYZE analysis_findings"))
        conn.execute(text("ANALYZE analytics_events"))
        conn.execute(text("ANALYZE citations"))
        conn.execute(text('ANALYZE "references"'))
    return created


def main() -> int:
    engine = create_engine(PG, pool_pre_ping=True, future=True)
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
        counts = {
            "assignments": int(conn.execute(text("SELECT COUNT(*) FROM assignments")).scalar() or 0),
            "findings": int(conn.execute(text("SELECT COUNT(*) FROM analysis_findings")).scalar() or 0),
            "citations": int(conn.execute(text("SELECT COUNT(*) FROM citations")).scalar() or 0),
            "references": int(conn.execute(text('SELECT COUNT(*) FROM "references"')).scalar() or 0),
            "analytics_events": int(conn.execute(text("SELECT COUNT(*) FROM analytics_events")).scalar() or 0),
        }
        user_id = conn.execute(text("SELECT user_id FROM assignments LIMIT 1")).scalar()
        report_id = conn.execute(text("SELECT id FROM analysis_reports LIMIT 1")).scalar()
        document_id = conn.execute(text("SELECT id FROM documents LIMIT 1")).scalar()
        cursor_row = conn.execute(
            text(
                "SELECT updated_at, id FROM assignments "
                "WHERE user_id = :uid AND deleted_at IS NULL "
                "ORDER BY updated_at DESC, id DESC LIMIT 1 OFFSET 19"
            ),
            {"uid": user_id},
        ).mappings().first()
        deep_cursor = conn.execute(
            text(
                "SELECT updated_at, id FROM assignments "
                "WHERE user_id = :uid AND deleted_at IS NULL "
                "ORDER BY updated_at DESC, id DESC LIMIT 1 OFFSET 49999"
            ),
            {"uid": user_id},
        ).mappings().first()
        finding_cursor = conn.execute(
            text(
                "SELECT created_at, id FROM analysis_findings "
                "WHERE report_id = :rid ORDER BY created_at ASC, id ASC LIMIT 1 OFFSET 39"
            ),
            {"rid": report_id},
        ).mappings().first()
    indexes = ensure_keyset_indexes(engine)

    offset_sql = (
        "SELECT id, title, status FROM assignments "
        "WHERE user_id = :uid AND deleted_at IS NULL "
        "ORDER BY updated_at DESC, id DESC LIMIT 20 OFFSET :off"
    )
    keyset_sql = (
        "SELECT id, title, status FROM assignments "
        "WHERE user_id = :uid AND deleted_at IS NULL "
        "AND (updated_at, id) < (:ts, :rid) "
        "ORDER BY updated_at DESC, id DESC LIMIT 20"
    )
    findings_offset = (
        "SELECT id, category, severity FROM analysis_findings "
        "WHERE report_id = :rid ORDER BY created_at ASC, id ASC LIMIT 40 OFFSET :off"
    )
    findings_keyset = (
        "SELECT id, category, severity FROM analysis_findings "
        "WHERE report_id = :rid AND (created_at, id) > (:ts, :fid) "
        "ORDER BY created_at ASC, id ASC LIMIT 40"
    )

    queries = {
        "assignment_offset_20": timed(engine, offset_sql, {"uid": user_id, "off": 20}),
        "assignment_offset_50000": timed(engine, offset_sql, {"uid": user_id, "off": 50000}),
        "assignment_offset_99980": timed(engine, offset_sql, {"uid": user_id, "off": 99980}),
        "findings_offset_80": timed(engine, findings_offset, {"rid": report_id, "off": 80}),
        "findings_offset_500000": timed(engine, findings_offset, {"rid": report_id, "off": 500000}),
        "analytics_group": timed(
            engine,
            "SELECT event_name, COUNT(*) FROM analytics_events WHERE user_id = :uid GROUP BY event_name",
            {"uid": user_id},
            loops=8,
        ),
        "payments_list": timed(
            engine,
            "SELECT id, status FROM payments WHERE user_id = :uid ORDER BY created_at DESC LIMIT 50",
            {"uid": user_id},
        ),
    }
    if cursor_row:
        queries["assignment_keyset_page2"] = timed(
            engine,
            keyset_sql,
            {"uid": user_id, "ts": cursor_row["updated_at"], "rid": cursor_row["id"]},
        )
    if deep_cursor:
        queries["assignment_keyset_after_50k"] = timed(
            engine,
            keyset_sql,
            {"uid": user_id, "ts": deep_cursor["updated_at"], "rid": deep_cursor["id"]},
        )
    if finding_cursor:
        queries["findings_keyset_page2"] = timed(
            engine,
            findings_keyset,
            {"rid": report_id, "ts": finding_cursor["created_at"], "fid": finding_cursor["id"]},
        )

    plans = {
        "assignment_offset_20": explain(engine, offset_sql, {"uid": user_id, "off": 20}),
        "assignment_offset_50000": explain(engine, offset_sql, {"uid": user_id, "off": 50000}),
        "assignment_offset_99980": explain(engine, offset_sql, {"uid": user_id, "off": 99980}),
        "findings_offset_500000": explain(engine, findings_offset, {"rid": report_id, "off": 500000}),
        "analytics_group": explain(
            engine,
            "SELECT event_name, COUNT(*) FROM analytics_events WHERE user_id = :uid GROUP BY event_name",
            {"uid": user_id},
        ),
        "citation_page": explain(
            engine,
            "SELECT id, raw_text FROM citations WHERE document_id = :did ORDER BY id LIMIT 40 OFFSET 80",
            {"did": document_id},
        ),
        "reference_page": explain(
            engine,
            'SELECT id, raw_text FROM "references" WHERE document_id = :did ORDER BY sort_order LIMIT 40',
            {"did": document_id},
        ),
    }
    if cursor_row:
        plans["assignment_keyset_page2"] = explain(
            engine,
            keyset_sql,
            {"uid": user_id, "ts": cursor_row["updated_at"], "rid": cursor_row["id"]},
        )
    if deep_cursor:
        plans["assignment_keyset_after_50k"] = explain(
            engine,
            keyset_sql,
            {"uid": user_id, "ts": deep_cursor["updated_at"], "rid": deep_cursor["id"]},
        )

    def seq_only(plan: str) -> bool:
        first = plan.split("\n")[0]
        return "Seq Scan" in plan and "Index" not in first

    payload = {
        "measured_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "engine": "postgresql-16",
        "host": "docker postgres:16-alpine on 127.0.0.1:55432",
        "counts": counts,
        "indexes_ensured": indexes,
        "queries": queries,
        "explain_analyze": plans,
        "leading_seq_scan_only": {name: seq_only(plan) for name, plan in plans.items()},
        "not_run": ["findings_5000000", "findings_10000000", "read_replica", "pgbouncer"],
    }
    out = ROOT / "ops" / "cert_postgres_keyset.json"
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    summary = {k: payload[k] for k in ("counts", "queries", "leading_seq_scan_only", "not_run")}
    print(json.dumps(summary, indent=2))
    engine.dispose()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
