"""PostgreSQL certification harness. Writes only measured numbers."""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

PG = os.environ.get(
    "CERT_DATABASE_URL",
    "postgresql+psycopg://academiccheck:academiccheck@127.0.0.1:55432/academiccheck",
)
os.environ["DATABASE_URL"] = PG
os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("APP_SECRET_KEY", "cert-secret")
os.environ.setdefault("JWT_SECRET_KEY", "cert-jwt-secret-key-32-bytes-min")

from sqlalchemy import create_engine, text  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app import models  # noqa: F401, E402
from app.db.session import Base  # noqa: E402
from app.models.admin import AnalyticsEvent  # noqa: E402
from app.models.analysis import AnalysisJob, AnalysisReport  # noqa: E402
from app.models.assignment import Assignment  # noqa: E402
from app.models.billing import Credit, Payment, Plan, Subscription  # noqa: E402
from app.models.citation import Citation, Reference  # noqa: E402
from app.models.document import Document  # noqa: E402
from app.models.user import User  # noqa: E402


def pct(samples: list[float], p: float) -> float:
    ordered = sorted(samples)
    return ordered[min(len(ordered) - 1, int((len(ordered) - 1) * p / 100))]


def timed(fn, loops: int = 20) -> dict:
    samples = []
    for _ in range(loops):
        start = time.perf_counter()
        fn()
        samples.append((time.perf_counter() - start) * 1000)
    return {
        "n": loops,
        "p50_ms": round(pct(samples, 50), 3),
        "p95_ms": round(pct(samples, 95), 3),
        "p99_ms": round(pct(samples, 99), 3),
        "max_ms": round(max(samples), 3),
    }


def copy_rows(engine, sql: str, rows_iter, total: int, label: str) -> float:
    start = time.perf_counter()
    remaining = total
    chunk = 50_000
    raw = engine.raw_connection()
    try:
        with raw.cursor() as cur:
            cur.execute("SET synchronous_commit TO OFF")
            while remaining > 0:
                take = min(chunk, remaining)
                with cur.copy(sql) as copy:
                    for _ in range(take):
                        copy.write_row(next(rows_iter))
                remaining -= take
                raw.commit()
                print(f"  {label} inserted {total - remaining}/{total}", flush=True)
    finally:
        raw.close()
    return time.perf_counter() - start


def explain(engine, sql: str, params: dict) -> str:
    with engine.connect() as conn:
        plan = conn.execute(text("EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT) " + sql), params)
        return "\n".join(row[0] for row in plan)


def main() -> int:
    engine = create_engine(PG, pool_size=10, max_overflow=20, pool_pre_ping=True, future=True)
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
        conn.commit()
    Base.metadata.create_all(bind=engine)

    with Session(engine) as db:
        user = db.query(User).filter(User.email == "cert-pg@example.com").one_or_none()
        if user is None:
            user = User(email="cert-pg@example.com", password_hash="x", full_name="Cert")
            db.add(user)
            db.flush()
        user_id = user.id
        plan = db.query(Plan).filter(Plan.slug == "cert-free").one_or_none()
        if plan is None:
            plan = Plan(slug="cert-free", name="Cert Free", price_usd_cents=0, checks_per_month=1000)
            db.add(plan)
            db.flush()
        plan_id = plan.id
        if db.query(Subscription).filter(Subscription.user_id == user_id).count() == 0:
            db.add(Subscription(user_id=user_id, plan_id=plan_id, status="active", provider="internal"))
        if db.query(Credit).filter(Credit.user_id == user_id).count() == 0:
            db.add(Credit(user_id=user_id, remaining=100, reserved=0))
        if db.query(Payment).filter(Payment.user_id == user_id).count() == 0:
            db.add(
                Payment(
                    user_id=user_id,
                    provider="internal",
                    amount_cents=0,
                    currency="USD",
                    status="successful",
                    purpose="cert",
                )
            )
        db.commit()

    inserts = {}
    for count in (10_000, 100_000):
        start = time.perf_counter()
        with Session(engine) as db:
            existing = db.scalar(text("SELECT COUNT(*) FROM assignments")) or 0
        need = count - int(existing)
        if need > 0:
            uid = str(user_id)

            def assignment_rows():
                while True:
                    yield (str(uuid4()), uid, "Assignment cert", "undergraduate", "apa7", "draft", "")

            elapsed = copy_rows(
                engine,
                "COPY assignments (id, user_id, title, academic_level, citation_style, status, notes) FROM STDIN",
                assignment_rows(),
                need,
                f"assignments->{count}",
            )
            inserts[f"assignments_{count}"] = {"added": need, "elapsed_s": round(elapsed, 3)}
        else:
            inserts[f"assignments_{count}"] = {"added": 0, "elapsed_s": round(time.perf_counter() - start, 3)}

    with Session(engine) as db:
        job = AnalysisJob(user_id=user_id, status="completed")
        db.add(job)
        db.flush()
        report = AnalysisReport(job_id=job.id, user_id=user_id, summary="cert")
        db.add(report)
        assignment = db.scalar(text("SELECT id FROM assignments LIMIT 1"))
        document = Document(
            user_id=user_id,
            filename="draft.txt",
            original_filename="draft.txt",
            mime_type="text/plain",
            extension=".txt",
            storage_key=f"{user_id}/draft.txt",
            extracted_text="Globalization has mixed effects on developing economies because trade rules differ.",
            normalized_text="Globalization has mixed effects on developing economies because trade rules differ.",
            word_count=12,
            status="extracted",
        )
        db.add(document)
        db.commit()
        report_id = report.id
        document_id = document.id

    findings_sql = (
        "COPY analysis_findings (id, report_id, category, severity, location, original_text, "
        "explanation, suggestion, teaching_note, example, improved_sentence, confidence) FROM STDIN"
    )
    rid = str(report_id)

    def finding_rows():
        while True:
            yield (
                str(uuid4()),
                rid,
                "thesis",
                "medium",
                "",
                "",
                "bench finding",
                "",
                "",
                "",
                "",
                70,
            )

    findings_targets = [1_000_000]
    extra = os.environ.get("CERT_FINDINGS_EXTRA", "")
    if extra:
        findings_targets.extend(int(x) for x in extra.split(",") if x.strip())
    for count in findings_targets:
        with Session(engine) as db:
            existing = int(db.scalar(text("SELECT COUNT(*) FROM analysis_findings")) or 0)
        need = count - existing
        elapsed = 0.0
        if need > 0:
            print(f"inserting {need} findings to reach {count}", flush=True)
            elapsed = copy_rows(engine, findings_sql, finding_rows(), need, f"findings->{count}")
        inserts[f"findings_{count}"] = {"added": max(need, 0), "elapsed_s": round(elapsed, 3), "total": count}

    did = str(document_id)
    uid = str(user_id)
    related = {
        "citations": (
            100_000,
            "COPY citations (id, document_id, raw_text, char_start, char_end) FROM STDIN",
            lambda: (str(uuid4()), did, "(Rodrik, 2011)", 0, 14),
        ),
        "references": (
            50_000,
            'COPY "references" (id, document_id, raw_text, missing_fields, sort_order) FROM STDIN',
            lambda: (str(uuid4()), did, "Rodrik, D. (2011). The globalization paradox.", "", 0),
        ),
        "analytics_events": (
            100_000,
            "COPY analytics_events (id, user_id, event_name, properties) FROM STDIN",
            lambda: (str(uuid4()), uid, "dashboard_view", "{}"),
        ),
    }
    for table, (target, sql, row_fn) in related.items():
        quoted = f'"{table}"' if table == "references" else table
        with Session(engine) as db:
            existing = int(db.scalar(text(f"SELECT COUNT(*) FROM {quoted}")) or 0)
        need = target - existing
        if need > 0:

            def rows(fn=row_fn):
                while True:
                    yield fn()

            elapsed = copy_rows(engine, sql, rows(), need, table)
            inserts[table] = {"added": need, "elapsed_s": round(elapsed, 3), "total": target}
        else:
            inserts[table] = {"added": 0, "elapsed_s": 0, "total": existing}

    with engine.begin() as conn:
        conn.execute(text("ANALYZE"))

    queries = {}
    with Session(engine) as db:

        def list_assignments():
            db.execute(
                text(
                    "SELECT id, title, status FROM assignments "
                    "WHERE user_id = :uid AND deleted_at IS NULL "
                    "ORDER BY updated_at DESC LIMIT 20 OFFSET 40"
                ),
                {"uid": user_id},
            ).fetchall()

        def page_findings():
            db.execute(
                text(
                    "SELECT id, category, severity FROM analysis_findings "
                    "WHERE report_id = :rid ORDER BY created_at ASC LIMIT 40 OFFSET 80"
                ),
                {"rid": report_id},
            ).fetchall()

        def list_reports():
            db.execute(
                text(
                    "SELECT id, overall_score FROM analysis_reports "
                    "WHERE user_id = :uid ORDER BY created_at DESC LIMIT 20"
                ),
                {"uid": user_id},
            ).fetchall()

        def page_citations():
            db.execute(
                text("SELECT id, raw_text FROM citations WHERE document_id = :did ORDER BY id LIMIT 40 OFFSET 80"),
                {"did": document_id},
            ).fetchall()

        def page_references():
            db.execute(
                text('SELECT id, raw_text FROM "references" WHERE document_id = :did ORDER BY sort_order LIMIT 40'),
                {"did": document_id},
            ).fetchall()

        def analytics_by_event():
            db.execute(
                text(
                    "SELECT event_name, COUNT(*) FROM analytics_events "
                    "WHERE user_id = :uid GROUP BY event_name"
                ),
                {"uid": user_id},
            ).fetchall()

        queries["assignment_list_100k"] = timed(list_assignments, 15)
        queries["findings_page"] = timed(page_findings, 15)
        queries["report_list"] = timed(list_reports, 15)
        queries["citation_page"] = timed(page_citations, 15)
        queries["reference_page"] = timed(page_references, 15)
        queries["analytics_group"] = timed(analytics_by_event, 10)

    plans = {
        "assignment_list": explain(
            engine,
            "SELECT id, title, status FROM assignments WHERE user_id = :uid AND deleted_at IS NULL "
            "ORDER BY updated_at DESC LIMIT 20 OFFSET 40",
            {"uid": user_id},
        ),
        "findings_page": explain(
            engine,
            "SELECT id, category, severity FROM analysis_findings WHERE report_id = :rid "
            "ORDER BY created_at ASC LIMIT 40 OFFSET 80",
            {"rid": report_id},
        ),
        "report_list": explain(
            engine,
            "SELECT id, overall_score FROM analysis_reports WHERE user_id = :uid "
            "ORDER BY created_at DESC LIMIT 20",
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
        "analytics_group": explain(
            engine,
            "SELECT event_name, COUNT(*) FROM analytics_events WHERE user_id = :uid GROUP BY event_name",
            {"uid": user_id},
        ),
    }
    seq_scans = {name: ("Seq Scan" in plan and "Index" not in plan.split("\n")[0]) for name, plan in plans.items()}

    pool_storm = {"n": 40, "errors": 0, "p95_ms": None}
    storm_samples: list[float] = []
    from concurrent.futures import ThreadPoolExecutor, as_completed

    def one_select() -> float:
        t0 = time.perf_counter()
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return (time.perf_counter() - t0) * 1000

    with ThreadPoolExecutor(max_workers=40) as pool:
        futs = [pool.submit(one_select) for _ in range(80)]
        for fut in as_completed(futs):
            try:
                storm_samples.append(fut.result())
            except Exception:
                pool_storm["errors"] += 1
    if storm_samples:
        pool_storm["p95_ms"] = round(pct(storm_samples, 95), 3)
        pool_storm["max_ms"] = round(max(storm_samples), 3)

    with Session(engine) as db:
        counts = {
            "users": int(db.scalar(text("SELECT COUNT(*) FROM users")) or 0),
            "assignments": int(db.scalar(text("SELECT COUNT(*) FROM assignments")) or 0),
            "documents": int(db.scalar(text("SELECT COUNT(*) FROM documents")) or 0),
            "reports": int(db.scalar(text("SELECT COUNT(*) FROM analysis_reports")) or 0),
            "findings": int(db.scalar(text("SELECT COUNT(*) FROM analysis_findings")) or 0),
            "citations": int(db.scalar(text("SELECT COUNT(*) FROM citations")) or 0),
            "references": int(db.scalar(text('SELECT COUNT(*) FROM "references"')) or 0),
            "analytics_events": int(db.scalar(text("SELECT COUNT(*) FROM analytics_events")) or 0),
            "payments": int(db.scalar(text("SELECT COUNT(*) FROM payments")) or 0),
            "credits": int(db.scalar(text("SELECT COUNT(*) FROM credits")) or 0),
            "subscriptions": int(db.scalar(text("SELECT COUNT(*) FROM subscriptions")) or 0),
        }

    payload = {
        "measured_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "engine": "postgresql-16",
        "host": "docker postgres:16-alpine on 127.0.0.1:55432",
        "pool": {"pool_size": 10, "max_overflow": 20, "storm": pool_storm},
        "counts": counts,
        "inserts": inserts,
        "queries": queries,
        "explain_analyze": plans,
        "leading_seq_scan_only": seq_scans,
        "p95_query_target_ms": 100,
        "p95_pass": all(v["p95_ms"] < 100 for v in queries.values()),
        "partitioned": False,
        "read_replica": "not_provisioned",
    }
    have = set(inserts)
    payload["not_run"] = [
        name for name in ("findings_5000000", "findings_10000000") if name not in have
    ]
    out = ROOT / "ops" / "cert_postgres_results.json"
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps({k: payload[k] for k in ("counts", "inserts", "queries", "p95_pass", "not_run")}, indent=2))
    engine.dispose()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
