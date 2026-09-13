"""Load structurally realistic 5M/10M-row datasets into local Docker Postgres.

Every count in the artifact is from COUNT(*) after INSERT, not an estimate.
"""

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
    "postgresql+psycopg://academiccheck:academiccheck@127.0.0.1:56432/academiccheck",
)
TARGETS = {
    "findings_5m": int(os.environ.get("CERT_FINDINGS_5M", "5000000")),
    "findings_10m": int(os.environ.get("CERT_FINDINGS_10M", "10000000")),
    "analytics_5m": int(os.environ.get("CERT_ANALYTICS_5M", "5000000")),
    "assignments_1m": int(os.environ.get("CERT_ASSIGNMENTS_1M", "1000000")),
}

os.environ["DATABASE_URL"] = PG
os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("APP_SECRET_KEY", "cert-secret")
os.environ.setdefault("JWT_SECRET_KEY", "cert-jwt-secret-key-32-bytes-min")

from sqlalchemy import create_engine, text  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app import models  # noqa: F401, E402
from app.db.session import Base  # noqa: E402
from app.models.analysis import AnalysisJob, AnalysisReport  # noqa: E402
from app.models.assignment import Assignment  # noqa: E402
from app.models.document import Document  # noqa: E402
from app.models.user import User  # noqa: E402

CHUNK = int(os.environ.get("CERT_INSERT_CHUNK", "500000"))


def count(conn, sql: str, params: dict | None = None) -> int:
    return int(conn.execute(text(sql), params or {}).scalar() or 0)


def insert_series(engine, sql: str, start: int, end: int, label: str) -> float:
    t0 = time.perf_counter()
    with engine.begin() as conn:
        conn.execute(text("SET synchronous_commit TO OFF"))
        conn.execute(text(sql), {"start": start, "end": end})
    elapsed = time.perf_counter() - t0
    print(f"  {label} {start}-{end} in {elapsed:.1f}s", flush=True)
    return elapsed


def ensure_seed(engine) -> dict:
    with Session(engine) as db:
        user = db.query(User).filter(User.email == "scale-load@example.com").one_or_none()
        if user is None:
            user = User(email="scale-load@example.com", password_hash="x", full_name="Scale")
            db.add(user)
            db.flush()
        assignment = db.query(Assignment).filter(Assignment.user_id == user.id).first()
        if assignment is None:
            assignment = Assignment(user_id=user.id, title="Scale load", academic_level="undergraduate")
            db.add(assignment)
            db.flush()
        document = db.query(Document).filter(Document.user_id == user.id).first()
        if document is None:
            document = Document(
                user_id=user.id,
                assignment_id=assignment.id,
                filename="draft.txt",
                original_filename="draft.txt",
                mime_type="text/plain",
                extension=".txt",
                storage_key=f"{user.id}/draft.txt",
                extracted_text="Globalization has mixed effects on developing economies.",
                normalized_text="Globalization has mixed effects on developing economies.",
                word_count=8,
                status="extracted",
            )
            db.add(document)
            db.flush()
        job = db.query(AnalysisJob).filter(AnalysisJob.user_id == user.id).first()
        if job is None:
            job = AnalysisJob(
                user_id=user.id,
                assignment_id=assignment.id,
                document_id=document.id,
                status="completed",
                analysis_type="full",
            )
            db.add(job)
            db.flush()
        report = db.query(AnalysisReport).filter(AnalysisReport.user_id == user.id).first()
        if report is None:
            report = AnalysisReport(
                job_id=job.id,
                assignment_id=assignment.id,
                document_id=document.id,
                user_id=user.id,
                overall_score=62,
                summary="scale",
            )
            db.add(report)
            db.flush()
        db.commit()
        return {
            "user_id": str(user.id),
            "assignment_id": str(assignment.id),
            "document_id": str(document.id),
            "report_id": str(report.id),
        }


def grow_findings(engine, report_id: str, target: int) -> dict:
    with engine.connect() as conn:
        existing = count(conn, "SELECT COUNT(*) FROM analysis_findings WHERE report_id = CAST(:rid AS uuid)", {"rid": report_id})
    inserted = 0
    elapsed = 0.0
    next_start = existing + 1
    sql = """
        INSERT INTO analysis_findings (
            id, report_id, category, severity, location, paragraph,
            original_text, explanation, suggestion, teaching_note, example,
            improved_sentence, confidence, created_at, updated_at
        )
        SELECT
            gen_random_uuid(),
            CAST(:rid AS uuid),
            CASE (g % 3) WHEN 0 THEN 'structure' WHEN 1 THEN 'grammar' ELSE 'citation' END,
            CASE (g % 3) WHEN 0 THEN 'low' WHEN 1 THEN 'medium' ELSE 'high' END,
            'p',
            (g % 40),
            'o', 'e', 's', 'n', 'x', 'i',
            70,
            TIMESTAMPTZ '2020-01-01' + (g * INTERVAL '1 millisecond'),
            NOW()
        FROM generate_series(:start, :end) AS g
    """
    while next_start <= target:
        end = min(target, next_start + CHUNK - 1)
        bind = sql.replace("CAST(:rid AS uuid)", f"'{report_id}'::uuid")
        elapsed += insert_series(engine, bind, next_start, end, "findings")
        inserted += end - next_start + 1
        next_start = end + 1
    with engine.connect() as conn:
        actual = count(conn, "SELECT COUNT(*) FROM analysis_findings")
    return {"target": target, "inserted_this_run": inserted, "count_star": actual, "elapsed_s": round(elapsed, 3)}


def grow_analytics(engine, user_id: str, target: int) -> dict:
    with engine.connect() as conn:
        existing = count(conn, "SELECT COUNT(*) FROM analytics_events")
    inserted = 0
    elapsed = 0.0
    next_start = existing + 1
    sql = f"""
        INSERT INTO analytics_events (id, user_id, event_name, properties, path, created_at, updated_at)
        SELECT
            gen_random_uuid(),
            '{user_id}'::uuid,
            CASE (g % 4) WHEN 0 THEN 'landing_page_view' WHEN 1 THEN 'analysis_started'
                         WHEN 2 THEN 'analysis_completed' ELSE 'document_uploaded' END,
            '{{}}',
            '/check',
            TIMESTAMPTZ '2020-01-01' + (g * INTERVAL '1 millisecond'),
            NOW()
        FROM generate_series(:start, :end) AS g
    """
    while next_start <= target:
        end = min(target, next_start + CHUNK - 1)
        elapsed += insert_series(engine, sql, next_start, end, "analytics")
        inserted += end - next_start + 1
        next_start = end + 1
    with engine.connect() as conn:
        actual = count(conn, "SELECT COUNT(*) FROM analytics_events")
    return {"target": target, "inserted_this_run": inserted, "count_star": actual, "elapsed_s": round(elapsed, 3)}


def grow_assignments(engine, user_id: str, target: int) -> dict:
    with engine.connect() as conn:
        existing = count(conn, "SELECT COUNT(*) FROM assignments")
    inserted = 0
    elapsed = 0.0
    next_start = existing + 1
    sql = f"""
        INSERT INTO assignments (
            id, user_id, title, academic_level, citation_style, notes, status, created_at, updated_at
        )
        SELECT
            gen_random_uuid(),
            '{user_id}'::uuid,
            'A' || g,
            'undergraduate',
            'apa7',
            '',
            'draft',
            TIMESTAMPTZ '2020-01-01' + (g * INTERVAL '1 millisecond'),
            TIMESTAMPTZ '2020-01-01' + (g * INTERVAL '1 millisecond')
        FROM generate_series(:start, :end) AS g
    """
    while next_start <= target:
        end = min(target, next_start + CHUNK - 1)
        elapsed += insert_series(engine, sql, next_start, end, "assignments")
        inserted += end - next_start + 1
        next_start = end + 1
    with engine.connect() as conn:
        actual = count(conn, "SELECT COUNT(*) FROM assignments")
    return {"target": target, "inserted_this_run": inserted, "count_star": actual, "elapsed_s": round(elapsed, 3)}


def ensure_indexes(engine) -> None:
    statements = [
        "CREATE INDEX IF NOT EXISTS ix_assignments_user_updated_id ON assignments (user_id, updated_at, id) WHERE deleted_at IS NULL",
        "CREATE INDEX IF NOT EXISTS ix_analysis_findings_report_created_id ON analysis_findings (report_id, created_at, id)",
        "CREATE INDEX IF NOT EXISTS ix_analytics_events_user_event ON analytics_events (user_id, event_name)",
    ]
    with engine.begin() as conn:
        for sql in statements:
            conn.execute(text(sql))
        conn.execute(text("ANALYZE assignments"))
        conn.execute(text("ANALYZE analysis_findings"))
        conn.execute(text("ANALYZE analytics_events"))


def main() -> int:
    engine = create_engine(PG, pool_pre_ping=True, future=True)
    t0 = time.perf_counter()
    Base.metadata.create_all(bind=engine)
    ids = ensure_seed(engine)
    payload: dict = {
        "measured_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "database_url_host": "127.0.0.1:56432",
        "ids": ids,
        "stages": {},
        "not_reached": [],
    }
    try:
        payload["stages"]["findings_5m"] = grow_findings(engine, ids["report_id"], TARGETS["findings_5m"])
        payload["stages"]["assignments_1m"] = grow_assignments(engine, ids["user_id"], TARGETS["assignments_1m"])
        payload["stages"]["analytics_5m"] = grow_analytics(engine, ids["user_id"], TARGETS["analytics_5m"])
        ensure_indexes(engine)
        payload["stages"]["findings_10m"] = grow_findings(engine, ids["report_id"], TARGETS["findings_10m"])
        ensure_indexes(engine)
    except Exception as exc:
        payload["load_error"] = str(exc)
        print(f"LOAD STOPPED: {exc}", flush=True)
    with engine.connect() as conn:
        payload["final_counts"] = {
            "assignments": count(conn, "SELECT COUNT(*) FROM assignments"),
            "analysis_findings": count(conn, "SELECT COUNT(*) FROM analysis_findings"),
            "analytics_events": count(conn, "SELECT COUNT(*) FROM analytics_events"),
            "users": count(conn, "SELECT COUNT(*) FROM users"),
        }
        for name, target in (
            ("findings_5m", TARGETS["findings_5m"]),
            ("findings_10m", TARGETS["findings_10m"]),
            ("analytics_5m", TARGETS["analytics_5m"]),
            ("assignments_1m", TARGETS["assignments_1m"]),
        ):
            table = {
                "findings_5m": "analysis_findings",
                "findings_10m": "analysis_findings",
                "analytics_5m": "analytics_events",
                "assignments_1m": "assignments",
            }[name]
            actual = payload["final_counts"][table]
            if actual < target:
                payload["not_reached"].append({"cell": name, "target": target, "actual": actual})
    payload["elapsed_s"] = round(time.perf_counter() - t0, 3)
    out = ROOT / "ops" / "cert_scale_5m_rows.json"
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps({"final_counts": payload["final_counts"], "not_reached": payload["not_reached"]}, indent=2))
    engine.dispose()
    return 0 if not payload["not_reached"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
