"""Re-time citation/reference/analytics queries after 006 indexes. Does not reload 1M findings."""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
os.environ["DATABASE_URL"] = os.environ.get(
    "CERT_DATABASE_URL",
    "postgresql+psycopg://academiccheck:academiccheck@127.0.0.1:55432/academiccheck",
)
os.environ.setdefault("APP_ENV", "test")

from sqlalchemy import create_engine, text  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402


def pct(samples: list[float], p: float) -> float:
    ordered = sorted(samples)
    return ordered[min(len(ordered) - 1, int((len(ordered) - 1) * p / 100))]


def timed(fn, loops: int = 15) -> dict:
    samples = []
    for _ in range(loops):
        start = time.perf_counter()
        fn()
        samples.append((time.perf_counter() - start) * 1000)
    return {"n": loops, "p50_ms": round(pct(samples, 50), 3), "p95_ms": round(pct(samples, 95), 3)}


def explain(engine, sql: str, params: dict) -> str:
    with engine.connect() as conn:
        plan = conn.execute(text("EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT) " + sql), params)
        return "\n".join(row[0] for row in plan)


def main() -> int:
    engine = create_engine(os.environ["DATABASE_URL"], future=True)
    with Session(engine) as db:
        uid = db.scalar(text("SELECT id FROM users WHERE email = 'cert-pg@example.com'"))
        did = db.scalar(text("SELECT id FROM documents LIMIT 1"))
    with Session(engine) as db:
        queries = {
            "citation_page": timed(
                lambda: db.execute(
                    text("SELECT id, raw_text FROM citations WHERE document_id = :did ORDER BY id LIMIT 40 OFFSET 80"),
                    {"did": did},
                ).fetchall()
            ),
            "reference_page": timed(
                lambda: db.execute(
                    text(
                        'SELECT id, raw_text FROM "references" WHERE document_id = :did ORDER BY sort_order LIMIT 40'
                    ),
                    {"did": did},
                ).fetchall()
            ),
            "analytics_group": timed(
                lambda: db.execute(
                    text(
                        "SELECT event_name, COUNT(*) FROM analytics_events WHERE user_id = :uid GROUP BY event_name"
                    ),
                    {"uid": uid},
                ).fetchall(),
                10,
            ),
        }
    plans = {
        "citation_page": explain(
            engine,
            "SELECT id, raw_text FROM citations WHERE document_id = :did ORDER BY id LIMIT 40 OFFSET 80",
            {"did": did},
        ),
        "reference_page": explain(
            engine,
            'SELECT id, raw_text FROM "references" WHERE document_id = :did ORDER BY sort_order LIMIT 40',
            {"did": did},
        ),
        "analytics_group": explain(
            engine,
            "SELECT event_name, COUNT(*) FROM analytics_events WHERE user_id = :uid GROUP BY event_name",
            {"uid": uid},
        ),
    }
    payload = {
        "measured_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "after_006_indexes": True,
        "queries": queries,
        "explain_analyze": plans,
        "index_scan": {name: "Index" in plan.split("\n")[1] or "Index" in plan.split("\n")[0] for name, plan in plans.items()},
        "p95_pass": all(v["p95_ms"] < 100 for v in queries.values()),
    }
    out = ROOT / "ops" / "cert_postgres_index_after.json"
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps({"queries": queries, "p95_pass": payload["p95_pass"], "plans_head": {k: v.split(chr(10))[0:3] for k, v in plans.items()}}, indent=2))
    engine.dispose()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
