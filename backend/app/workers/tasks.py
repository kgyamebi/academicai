from uuid import UUID

from app.db.session import SessionLocal
from app.services.analysis.runner import process_job


def run_analysis_job(job_id: str) -> None:
    db = SessionLocal()
    try:
        process_job(db, UUID(job_id))
    finally:
        db.close()
