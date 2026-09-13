"""Local scalability benches. Writes measured numbers only. Does not invent 50k-user results."""

from __future__ import annotations

import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))
os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("APP_SECRET_KEY", "bench-secret")
os.environ.setdefault("JWT_SECRET_KEY", "bench-jwt-secret-key-32-bytes-min")
os.environ.setdefault("DATABASE_URL", "sqlite:///./bench_scale.db")
os.environ.setdefault("REDIS_URL", "redis://127.0.0.1:6379/14")

from sqlalchemy import create_engine, event, text  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app.db.session import Base  # noqa: E402
from app.models.analysis import AnalysisFinding, AnalysisJob, AnalysisReport  # noqa: E402
from app.models.assignment import Assignment  # noqa: E402
from app.models.user import User  # noqa: E402
from app.services.ai.cache import cache_key, get_cached, reset_cache, set_cached  # noqa: E402
from app.services.ai.provider import AIResponse  # noqa: E402
from app.services.analysis.engine import run_analysis  # noqa: E402
from app.services.documents.extractor import ExtractedDocument, ExtractedParagraph, ExtractedSection  # noqa: E402


def pct(samples: list[float], p: float) -> float:
    if not samples:
        return 0.0
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


def bench_database() -> dict:
    db_path = BACKEND / "bench_scale.db"
    if db_path.exists():
        db_path.unlink()
    engine = create_engine(f"sqlite:///{db_path}", future=True)
    if engine.dialect.name == "sqlite":

        @event.listens_for(engine, "connect")
        def _fk(dbapi_conn, _rec):  # noqa: ANN001
            dbapi_conn.execute("PRAGMA journal_mode=WAL")
            dbapi_conn.execute("PRAGMA synchronous=OFF")

    Base.metadata.create_all(bind=engine)
    results: dict = {"engine": "sqlite", "inserts": {}, "queries": {}}
    user_id = uuid4()
    with Session(engine) as db:
        db.add(User(id=user_id, email="bench@example.com", password_hash="x", full_name="Bench"))
        db.commit()

    for count in (10_000, 50_000, 100_000):
        start = time.perf_counter()
        with Session(engine) as db:
            existing = db.scalar(text("SELECT COUNT(*) FROM assignments")) or 0
        need = count - int(existing)
        if need > 0:
            chunk = [
                {
                    "id": uuid4(),
                    "user_id": user_id,
                    "title": f"Assignment {i}",
                    "academic_level": "undergraduate",
                    "citation_style": "apa7",
                    "status": "draft",
                }
                for i in range(need)
            ]
            with engine.begin() as conn:
                conn.execute(Assignment.__table__.insert(), chunk)
        results["inserts"][f"assignments_{count}"] = {
            "added": max(need, 0),
            "elapsed_s": round(time.perf_counter() - start, 3),
        }

        with Session(engine) as db:

            def list_page():
                db.execute(
                    text(
                        "SELECT id, title, status FROM assignments "
                        "WHERE user_id = :uid AND deleted_at IS NULL "
                        "ORDER BY updated_at DESC LIMIT 20 OFFSET 40"
                    ),
                    {"uid": str(user_id)},
                ).fetchall()

            results["queries"][f"assignment_list_{count}"] = timed(list_page, 15)

    # Findings scale: attach to one report
    with Session(engine) as db:
        job = AnalysisJob(user_id=user_id, status="completed")
        db.add(job)
        db.flush()
        report = AnalysisReport(job_id=job.id, user_id=user_id, summary="bench")
        db.add(report)
        db.commit()
        report_id = report.id

    for count in (100_000, 500_000):
        start = time.perf_counter()
        with Session(engine) as db:
            existing = db.scalar(text("SELECT COUNT(*) FROM analysis_findings")) or 0
        need = count - int(existing)
        if need > 0:
            chunk_size = 20_000
            remaining = need
            while remaining > 0:
                take = min(chunk_size, remaining)
                payload = [
                    {
                        "id": uuid4(),
                        "report_id": report_id,
                        "category": "thesis",
                        "severity": "medium",
                        "explanation": "bench finding",
                    }
                    for _ in range(take)
                ]
                with engine.begin() as conn:
                    conn.execute(AnalysisFinding.__table__.insert(), payload)
                remaining -= take
        results["inserts"][f"findings_{count}"] = {
            "added": max(need, 0),
            "elapsed_s": round(time.perf_counter() - start, 3),
        }
        with Session(engine) as db:

            def page_findings():
                db.execute(
                    text(
                        "SELECT id, category, severity FROM analysis_findings "
                        "WHERE report_id = :rid ORDER BY created_at ASC LIMIT 40 OFFSET 80"
                    ),
                    {"rid": str(report_id)},
                ).fetchall()

            results["queries"][f"findings_page_{count}"] = timed(page_findings, 15)

    results["not_run"] = ["findings_5_000_000", "findings_10_000_000", "postgres_explain"]
    engine.dispose()
    return results


def _sample_doc() -> ExtractedDocument:
    paragraphs = [
        ExtractedParagraph(0, "Introduction", True, 1, 0, 12, 1),
        ExtractedParagraph(
            1,
            "This essay argues that globalization produces uneven development because trade rules favour capital over labour.",
            False,
            0,
            13,
            140,
            18,
        ),
        ExtractedParagraph(
            2,
            "For example, Stiglitz (2002) shows that capital account liberalisation can increase volatility in developing economies.",
            False,
            0,
            141,
            280,
            20,
        ),
        ExtractedParagraph(3, "References", True, 1, 281, 291, 1),
        ExtractedParagraph(4, "Stiglitz, J. (2002). Globalization and its discontents. Norton.", False, 0, 292, 360, 10),
    ]
    sections = [
        ExtractedSection("Introduction", "introduction", 0, 2, 0),
        ExtractedSection("References", "references", 3, 4, 1),
    ]
    body = " ".join(p.text for p in paragraphs)
    return ExtractedDocument(
        text=body,
        normalized_text=body,
        paragraphs=paragraphs,
        sections=sections,
        word_count=49,
        word_count_excl_references=39,
        word_count_excl_headings=38,
        paragraph_count=5,
        sentence_count=3,
        page_count=1,
        language="en",
    )


def bench_workers() -> dict:
    question = "Compare and evaluate the effects of globalization on developing economies."
    doc = _sample_doc()
    run_analysis(doc, question)  # warmup
    counts = (1, 5, 10, 25)
    out = {}
    for workers in counts:
        jobs = workers * 4
        start = time.perf_counter()
        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = [pool.submit(run_analysis, doc, question) for _ in range(jobs)]
            for future in as_completed(futures):
                future.result()
        elapsed = time.perf_counter() - start
        out[f"workers_{workers}"] = {
            "jobs": jobs,
            "elapsed_s": round(elapsed, 3),
            "jobs_per_min": round(jobs / elapsed * 60, 1),
            "avg_completion_s": round(elapsed / jobs, 3),
        }
    out["not_run"] = ["workers_50", "workers_100", "queue_lag_with_redis"]
    return out


def bench_ai_cache() -> dict:
    reset_cache()
    key = cache_key("identical prompt", strong=False)
    set_cached(key, AIResponse("{}", "bench", "cache", 1))
    start = time.perf_counter()
    hits = 0
    for _ in range(1000):
        if get_cached(key) is not None:
            hits += 1
    elapsed = (time.perf_counter() - start) * 1000
    return {"hits": hits, "lookups": 1000, "elapsed_ms": round(elapsed, 3), "per_lookup_us": round(elapsed / 10, 3)}


def bench_http() -> dict:
    from fastapi.testclient import TestClient

    from app.main import app

    client = TestClient(app)
    client.get("/api/live")
    samples = []
    errors = 0
    for _ in range(200):
        start = time.perf_counter()
        response = client.get("/api/live")
        samples.append((time.perf_counter() - start) * 1000)
        if response.status_code != 200:
            errors += 1
    concurrent = {}
    for users in (50, 100, 250):
        lat = []
        err = 0

        def one(_i=0):
            t0 = time.perf_counter()
            code = client.get("/api/live").status_code
            return (time.perf_counter() - t0) * 1000, code

        with ThreadPoolExecutor(max_workers=users) as pool:
            futs = [pool.submit(one) for _ in range(users)]
            for fut in as_completed(futs):
                ms, code = fut.result()
                lat.append(ms)
                if code != 200:
                    err += 1
        concurrent[str(users)] = {
            "in_flight": users,
            "p50_ms": round(pct(lat, 50), 3),
            "p95_ms": round(pct(lat, 95), 3),
            "p99_ms": round(pct(lat, 99), 3),
            "error_rate": round(err / max(len(lat), 1), 4),
            "note": "Starlette TestClient in one process — not a multi-node 10k-user result",
        }
    return {
        "sequential_200": {
            "p50_ms": round(pct(samples, 50), 3),
            "p95_ms": round(pct(samples, 95), 3),
            "p99_ms": round(pct(samples, 99), 3),
            "error_rate": round(errors / 200, 4),
        },
        "concurrent_testclient": concurrent,
        "not_run": ["1000_concurrent_users", "10000_concurrent_users", "50000_concurrent_users", "k6_against_staging"],
    }


def main() -> int:
    payload = {
        "measured_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "host": "local sqlite / TestClient",
        "database": bench_database(),
        "workers": bench_workers(),
        "ai_cache": bench_ai_cache(),
        "http": bench_http(),
    }
    out = ROOT / "ops" / "bench_results.json"
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
