"""Live Redis/RQ certification. Refuses to invent success if workers are missing."""

from __future__ import annotations

import json
import os
import subprocess
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
REDIS = os.environ.get("CERT_REDIS_URL", "redis://127.0.0.1:56379/0")
JOBS = int(os.environ.get("CERT_QUEUE_JOBS", "1000"))
WORKERS = int(os.environ.get("CERT_QUEUE_WORKERS", "5"))

os.environ["DATABASE_URL"] = PG
os.environ["REDIS_URL"] = REDIS
os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("APP_SECRET_KEY", "cert-secret")
os.environ.setdefault("JWT_SECRET_KEY", "cert-jwt-secret-key-32-bytes-min")
os.environ["REQUIRE_QUEUE"] = "false"

from redis import Redis  # noqa: E402
from rq import Queue, Worker  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app import models  # noqa: F401, E402
from app.db.session import Base  # noqa: E402
from app.models.analysis import AnalysisJob  # noqa: E402
from app.models.assignment import Assignment  # noqa: E402
from app.models.document import Document  # noqa: E402
from app.models.user import User  # noqa: E402

ESSAY = (
    "Globalization has changed trade in developing economies. This essay argues that the effects are mixed: "
    "export growth often rises, but inequality can widen unless industrial policy is strong. "
    "East Asian industrialisers used trade alongside policy (Rodrik, 2011)."
)


def main() -> int:
    redis = Redis.from_url(REDIS, socket_timeout=2)
    redis.ping()
    stale = Queue("analysis", connection=redis)
    stale.empty()
    Queue("analysis_dlq", connection=redis).empty()
    engine = create_engine(PG, future=True)
    Base.metadata.create_all(bind=engine)

    env = os.environ.copy()
    env.update(
        {
            "DATABASE_URL": PG,
            "REDIS_URL": REDIS,
            "APP_ENV": "test",
            "APP_SECRET_KEY": "cert-secret",
            "JWT_SECRET_KEY": "cert-jwt-secret-key-32-bytes-min",
            "PYTHONPATH": str(BACKEND),
        }
    )
    log_dir = ROOT / "tmp" / "cert_workers"
    log_dir.mkdir(parents=True, exist_ok=True)
    procs = []
    for i in range(WORKERS):
        log = (log_dir / f"worker-{i}.log").open("w", encoding="utf-8")
        procs.append(
            subprocess.Popen(
                [sys.executable, "-m", "app.workers.rq_worker"],
                cwd=BACKEND,
                env=env,
                stdout=log,
                stderr=log,
            )
        )
    deadline_workers = time.time() + 20
    workers = []
    while time.time() < deadline_workers:
        workers = Worker.all(connection=redis)
        if workers:
            break
        time.sleep(0.4)
    if not workers:
        for proc in procs:
            proc.terminate()
        print("UNPROVEN: workers did not register")
        return 2

    from sqlalchemy import select
    from uuid import UUID as UUIDType

    ids = []
    with Session(engine) as db:
        user = User(email=f"queue-{uuid4().hex[:8]}@example.com", password_hash="x", full_name="Q")
        db.add(user)
        db.flush()
        assignment = Assignment(user_id=user.id, title="Queue cert", academic_level="undergraduate")
        db.add(assignment)
        db.flush()
        document = Document(
            user_id=user.id,
            assignment_id=assignment.id,
            filename="draft.txt",
            original_filename="draft.txt",
            mime_type="text/plain",
            extension=".txt",
            storage_key=f"{user.id}/draft.txt",
            extracted_text=ESSAY,
            normalized_text=ESSAY,
            word_count=40,
            status="extracted",
        )
        db.add(document)
        db.flush()
        jobs = [
            AnalysisJob(
                user_id=user.id,
                assignment_id=assignment.id,
                document_id=document.id,
                status="queued",
                analysis_type="full",
            )
            for _ in range(JOBS)
        ]
        db.add_all(jobs)
        db.flush()
        ids = [str(job.id) for job in jobs]
        db.commit()
    uuid_ids = [UUIDType(x) for x in ids]

    queue = Queue("analysis", connection=redis)
    t0 = time.perf_counter()
    for job_id in ids:
        queue.enqueue(
            "app.workers.tasks.run_analysis_job",
            job_id,
            job_id=job_id,
            job_timeout=600,
        )
    enqueue_s = time.perf_counter() - t0

    deadline = time.time() + max(600, int(JOBS / max(WORKERS, 1) * 1.5) + 120)
    statuses = {}
    while time.time() < deadline:
        with Session(engine) as db:
            rows = db.scalars(select(AnalysisJob).where(AnalysisJob.id.in_(uuid_ids))).all()
            statuses = {}
            for row in rows:
                statuses[row.status] = statuses.get(row.status, 0) + 1
        if statuses.get("completed", 0) + statuses.get("failed", 0) == JOBS:
            break
        time.sleep(0.5)

    elapsed = time.perf_counter() - t0

    with Session(engine) as db:
        rows = list(db.scalars(select(AnalysisJob).where(AnalysisJob.id.in_(uuid_ids))))
    statuses = {}
    for row in rows:
        statuses[row.status] = statuses.get(row.status, 0) + 1
    lost = JOBS - len(rows)
    duplicates = JOBS - len({str(r.id) for r in rows})
    stuck = statuses.get("queued", 0) + statuses.get("processing", 0)
    payload = {
        "measured_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "redis": REDIS,
        "workers_started": WORKERS,
        "workers_registered": len(workers),
        "jobs": JOBS,
        "enqueue_s": round(enqueue_s, 3),
        "elapsed_s": round(elapsed, 3),
        "throughput_jobs_per_min": round(JOBS / max(elapsed, 0.001) * 60, 1),
        "statuses": statuses,
        "lost": lost,
        "duplicate_ids": duplicates,
        "stuck": stuck,
        "dlq_depth": Queue("analysis_dlq", connection=redis).count,
        "pass_no_loss_dup_stuck": lost == 0 and duplicates == 0 and stuck == 0 and statuses.get("completed", 0) == JOBS,
        "not_run": [n for n in (5000, 10000, 50000) if JOBS < n],
    }
    out = ROOT / "ops" / "cert_queue_results.json"
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload, indent=2))
    for proc in procs:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
    engine.dispose()
    return 0 if payload["pass_no_loss_dup_stuck"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
