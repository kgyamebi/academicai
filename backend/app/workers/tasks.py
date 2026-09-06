from uuid import UUID

from app.db.session import SessionLocal
from app.services.analysis.runner import process_job


def run_analysis_job(job_id: str) -> None:
    db = SessionLocal()
    try:
        process_job(db, UUID(job_id))
    finally:
        db.close()


def record_poison_job(job_id: str, error: str) -> None:
    from app.core.logging import get_logger

    get_logger("queue.dlq").error("poison_analysis_job", job_id=job_id, error=error)
