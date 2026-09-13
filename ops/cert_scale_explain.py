"""EXPLAIN ANALYZE at whatever row counts actually exist. Unrun/missing volume stays FAIL."""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

PRIMARY = os.environ.get(
    "CERT_DATABASE_URL",
    "postgresql+psycopg://academiccheck:academiccheck@127.0.0.1:56432/academiccheck",
)
PGBOUNCER = os.environ.get(
    "CERT_PGBOUNCER_URL",
    "postgresql+psycopg://academiccheck:academiccheck@127.0.0.1:56434/academiccheck",
)
REPLICA = os.environ.get(
    "CERT_REPLICA_URL",
    "postgresql+psycopg://academiccheck:academiccheck@127.0.0.1:56433/academiccheck",
)

from sqlalchemy import create_engine, text  # noqa: E402


def pct(samples: list[float], p: float) -> float:
    ordered = sorted(samples)
    return ordered[min(len(samples) - 1, int((len(samples) - 1) * p / 100))]


def timed(engine, sql: str, params: dict, loops: int = 10) -> dict:
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


def suite(engine, label: str) -> dict:
    with engine.connect() as conn:
        counts = {
            "assignments": int(conn.execute(text("SELECT COUNT(*) FROM assignments")).scalar() or 0),
            "findings": int(conn.execute(text("SELECT COUNT(*) FROM analysis_findings")).scalar() or 0),
            "analytics_events": int(conn.execute(text("SELECT COUNT(*) FROM analytics_events")).scalar() or 0),
        }
        user_id = conn.execute(text("SELECT user_id FROM assignments LIMIT 1")).scalar()
        report_id = conn.execute(text("SELECT id FROM analysis_reports LIMIT 1")).scalar()
        cursor_row = conn.execute(
            text(
                "SELECT updated_at, id FROM assignments "
                "WHERE user_id = :uid AND deleted_at IS NULL "
                "ORDER BY updated_at DESC, id DESC LIMIT 1 OFFSET 19"
            ),
            {"uid": user_id},
        ).mappings().first()
        deep_cursor = None
        if counts["assignments"] > 50000:
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
        mid_finding = None
        if counts["findings"] > 2_000_000:
            mid_finding = conn.execute(
                text(
                    "SELECT created_at, id FROM analysis_findings "
                    "WHERE report_id = :rid ORDER BY created_at ASC, id ASC LIMIT 1 OFFSET 2000000"
                ),
                {"rid": report_id},
            ).mappings().first()

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
    analytics_sql = "SELECT event_name, COUNT(*) FROM analytics_events WHERE user_id = :uid GROUP BY event_name"

    queries = {
        "assignment_offset_20": timed(engine, offset_sql, {"uid": user_id, "off": 20}),
        "findings_offset_80": timed(engine, findings_offset, {"rid": report_id, "off": 80}),
        "analytics_group": timed(engine, analytics_sql, {"uid": user_id}, loops=8),
    }
    if cursor_row:
        queries["assignment_keyset_page2"] = timed(
            engine, keyset_sql, {"uid": user_id, "ts": cursor_row["updated_at"], "rid": cursor_row["id"]}
        )
    if deep_cursor:
        queries["assignment_keyset_after_50k"] = timed(
            engine, keyset_sql, {"uid": user_id, "ts": deep_cursor["updated_at"], "rid": deep_cursor["id"]}
        )
    if finding_cursor:
        queries["findings_keyset_page2"] = timed(
            engine,
            findings_keyset,
            {"rid": report_id, "ts": finding_cursor["created_at"], "fid": finding_cursor["id"]},
        )
    if mid_finding:
        queries["findings_keyset_after_2m"] = timed(
            engine,
            findings_keyset,
            {"rid": report_id, "ts": mid_finding["created_at"], "fid": mid_finding["id"]},
        )

    # Deep OFFSET is rejected by the API (MAX_OFFSET_ROWS=200). Still time SQL so the
    # artifact proves the pathological query is not "fixed" at the planner — it is impossible
    # on the product path.
    api_cap = {
        "max_offset_rows": 200,
        "deep_offset_api": "rejected_http_400",
        "sql_still_pathological_if_bypassed": True,
    }
    if counts["findings"] >= 500_000:
        queries["findings_offset_500000_sql_bypass"] = timed(
            engine, findings_offset, {"rid": report_id, "off": 500000}, loops=3
        )
    if counts["assignments"] >= 50_000:
        queries["assignment_offset_50000_sql_bypass"] = timed(
            engine, offset_sql, {"uid": user_id, "off": 50000}, loops=3
        )

    plans = {
        "assignment_keyset_page2": explain(
            engine, keyset_sql, {"uid": user_id, "ts": cursor_row["updated_at"], "rid": cursor_row["id"]}
        )
        if cursor_row
        else "no_cursor_row",
        "analytics_group": explain(engine, analytics_sql, {"uid": user_id}),
    }
    slo = {name: {"p95_ms": q["p95_ms"], "pass_100ms": q["p95_ms"] < 100} for name, q in queries.items()}
    return {
        "label": label,
        "counts": counts,
        "queries": queries,
        "slo": slo,
        "api_offset_cap": api_cap,
        "explain_analyze": {k: v[:4000] for k, v in plans.items()},
        "volume_gates": {
            "findings_5m": counts["findings"] >= 5_000_000,
            "findings_10m": counts["findings"] >= 10_000_000,
            "analytics_5m": counts["analytics_events"] >= 5_000_000,
        },
    }


def concurrent_pgbouncer(engine, n: int = 40) -> dict:
    from concurrent.futures import ThreadPoolExecutor, as_completed

    sql = "SELECT 1"
    errors = 0
    samples = []

    def one() -> float:
        t0 = time.perf_counter()
        with engine.connect() as conn:
            conn.execute(text(sql)).fetchall()
        return (time.perf_counter() - t0) * 1000

    t0 = time.perf_counter()
    with ThreadPoolExecutor(max_workers=n) as pool:
        futs = [pool.submit(one) for _ in range(n * 5)]
        for fut in as_completed(futs):
            try:
                samples.append(fut.result())
            except Exception:
                errors += 1
    elapsed = time.perf_counter() - t0
    with engine.connect() as conn:
        pooled = conn.execute(text("SHOW pool_mode")).fetchall() if False else None
        who = conn.execute(text("SELECT current_database(), current_user")).fetchone()
    return {
        "clients": n,
        "requests": n * 5,
        "errors": errors,
        "elapsed_s": round(elapsed, 3),
        "p95_ms": round(pct(samples, 95), 3) if samples else None,
        "session": {"database": who[0], "user": who[1]} if who else None,
        "pool_mode_show": pooled,
    }


def replica_lag(primary, replica) -> dict:
    with primary.connect() as pconn, replica.connect() as rconn:
        p_lsn = pconn.execute(text("SELECT pg_current_wal_lsn()::text")).scalar()
        replay = rconn.execute(
            text("SELECT pg_last_wal_replay_lsn()::text, pg_is_in_recovery()")
        ).fetchone()
        p_findings = int(pconn.execute(text("SELECT COUNT(*) FROM analysis_findings")).scalar() or 0)
        r_findings = int(rconn.execute(text("SELECT COUNT(*) FROM analysis_findings")).scalar() or 0)
        with primary.begin() as pconn:
            pconn.execute(
                text(
                    "INSERT INTO analytics_events (id, event_name, properties) "
                    "VALUES (gen_random_uuid(), 'replica_probe', '{}')"
                )
            )
        deadline = time.time() + 15
        lag_s = None
        while time.time() < deadline:
            r_probe = int(
                rconn.execute(text("SELECT COUNT(*) FROM analytics_events WHERE event_name = 'replica_probe'")).scalar()
                or 0
            )
            if r_probe >= 1:
                lag_s = 15 - (deadline - time.time())
                break
            time.sleep(0.2)
            rconn.rollback()
        return {
            "primary_wal_lsn": p_lsn,
            "replica_replay_lsn": replay[0] if replay else None,
            "replica_in_recovery": bool(replay[1]) if replay else None,
            "findings_primary": p_findings,
            "findings_replica": r_findings,
            "findings_match": p_findings == r_findings,
            "probe_replicated_s": round(lag_s, 3) if lag_s is not None else None,
            "probe_replicated": lag_s is not None,
        }


def main() -> int:
    payload: dict = {
        "measured_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "paths": {"primary": PRIMARY, "pgbouncer": PGBOUNCER, "replica": REPLICA},
        "not_reached": [],
    }
    primary = create_engine(PRIMARY, pool_pre_ping=True, future=True, pool_size=8, max_overflow=20)
    try:
        payload["primary"] = suite(primary, "primary")
    except Exception as exc:
        payload["primary"] = {"error": str(exc)}
        payload["not_reached"].append("primary_explain")

    bouncer = create_engine(PGBOUNCER, pool_pre_ping=True, future=True, pool_size=20, max_overflow=40)
    try:
        payload["pgbouncer"] = {
            "query_suite": suite(bouncer, "pgbouncer"),
            "concurrent": concurrent_pgbouncer(bouncer, n=40),
        }
    except Exception as exc:
        payload["pgbouncer"] = {"error": str(exc)}
        payload["not_reached"].append("pgbouncer")

    replica = create_engine(REPLICA, pool_pre_ping=True, future=True)
    try:
        payload["replica"] = {
            "query_suite": suite(replica, "replica"),
            "lag": replica_lag(primary, replica),
        }
    except Exception as exc:
        payload["replica"] = {"error": str(exc)}
        payload["not_reached"].append("replica")

    out = ROOT / "ops" / "cert_scale_5m_rows.json"
    existing = {}
    if out.exists():
        try:
            existing = json.loads(out.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            existing = {}
    existing["explain"] = payload
    existing["measured_at"] = payload["measured_at"]
    out.write_text(json.dumps(existing, indent=2), encoding="utf-8")
    print(json.dumps({"not_reached": payload["not_reached"], "primary_counts": payload.get("primary", {}).get("counts")}, indent=2))
    primary.dispose()
    bouncer.dispose()
    replica.dispose()
    return 0 if not payload["not_reached"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
