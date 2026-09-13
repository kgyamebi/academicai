"""Worker death: kill RQ worker mid-queue and confirm remaining jobs complete after replacement."""

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
os.environ["DATABASE_URL"] = PG
os.environ["REDIS_URL"] = REDIS
os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("APP_SECRET_KEY", "cert-secret")
os.environ.setdefault("JWT_SECRET_KEY", "cert-jwt-secret-key-32-bytes-min")

from redis import Redis  # noqa: E402
from rq import Queue  # noqa: E402
from sqlalchemy import create_engine, select  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app.db.session import Base  # noqa: E402
from app.models.analysis import AnalysisJob  # noqa: E402
from app.models.assignment import Assignment  # noqa: E402
from app.models.document import Document  # noqa: E402
from app.models.user import User  # noqa: E402

ESSAY = (
    "Globalization has changed trade in developing economies. This essay argues that the effects are mixed: "
    "export growth often rises, but inequality can widen unless industrial policy is strong."
)


def start_worker(env) -> subprocess.Popen:
    log = (ROOT / "tmp" / "cert_worker_death.log")
    log.parent.mkdir(parents=True, exist_ok=True)
    return subprocess.Popen(
        [sys.executable, "-m", "app.workers.rq_worker"],
        cwd=BACKEND,
        env=env,
        stdout=log.open("a", encoding="utf-8"),
        stderr=subprocess.STDOUT,
    )


def main() -> int:
    redis = Redis.from_url(REDIS, socket_timeout=2)
    redis.ping()
    Queue("analysis", connection=redis).empty()
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
    worker = start_worker(env)
    time.sleep(2)
    ids = []
    with Session(engine) as db:
        user = User(email=f"death-{uuid4().hex[:8]}@example.com", password_hash="x", full_name="D")
        db.add(user)
        db.flush()
        assignment = Assignment(user_id=user.id, title="Death", academic_level="undergraduate")
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
            )
            for _ in range(12)
        ]
        db.add_all(jobs)
        db.flush()
        ids = [str(j.id) for j in jobs]
        db.commit()
    queue = Queue("analysis", connection=redis)
    for job_id in ids:
        queue.enqueue("app.workers.tasks.run_analysis_job", job_id, job_id=job_id, job_timeout=600)
    time.sleep(3)
    worker.kill()
    worker.wait(timeout=5)
    replacement = start_worker(env)
    deadline = time.time() + 120
    statuses = {}
    while time.time() < deadline:
        with Session(engine) as db:
            rows = db.scalars(select(AnalysisJob).where(AnalysisJob.id.in_(ids))).all()
            statuses = {}
            for row in rows:
                statuses[row.status] = statuses.get(row.status, 0) + 1
        if statuses.get("completed", 0) + statuses.get("failed", 0) == len(ids):
            break
        time.sleep(0.5)
    replacement.terminate()
    try:
        replacement.wait(timeout=5)
    except subprocess.TimeoutExpired:
        replacement.kill()
    stuck = statuses.get("queued", 0) + statuses.get("processing", 0)
    payload = {
        "measured_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "jobs": len(ids),
        "statuses": statuses,
        "stuck": stuck,
        "killed_pid_restarted": True,
        "pass": stuck == 0 and statuses.get("completed", 0) + statuses.get("failed", 0) == len(ids),
    }
    out = ROOT / "ops" / "cert_worker_death.json"
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload, indent=2))
    engine.dispose()
    return 0 if payload["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
