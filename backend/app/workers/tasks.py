from uuid import UUID

from app.core.logging import get_logger
from app.db.session import SessionLocal
from app.services.analysis.runner import fail_job, process_job, reap_stale_jobs, recover_orphaned_jobs

log = get_logger("queue.dlq")


def run_send_email(to: str, subject: str, body: str, html: str | None = None) -> None:
    """RQ worker entrypoint for outbound email."""
    from app.services.emailer import deliver_email_now

    try:
        deliver_email_now(to, subject, body, html=html)
    except Exception as exc:  # noqa: BLE001
        log.error("run_send_email_failed", subject=subject, error=str(exc), exc_info=exc)
        from app.core.alerting import fire_alert

        try:
            fire_alert(
                "email_worker_failed",
                title="Email worker send failed",
                detail=f"{subject}: {str(exc)[:400]}",
                severity="critical",
            )
        except Exception:  # noqa: BLE001
            pass
        raise


def run_extract_job(document_id: str) -> None:
    from app.services.documents.extract_job import process_extract_job

    process_extract_job(document_id)


def run_analysis_job(job_id: str) -> None:
    db = SessionLocal()
    try:
        recovered = recover_orphaned_jobs(db)
        db.commit()
        if recovered:
            from app.workers.queue import enqueue_analysis

            for rid in recovered:
                enqueue_analysis(str(rid))
        process_job(db, UUID(job_id))
        db.commit()
    except Exception as exc:  # noqa: BLE001
        log.error("run_analysis_job_crashed", job_id=job_id, error=str(exc), exc_info=exc)
        from app.core.alerting import notify_worker_failure

        notify_worker_failure(job_id=str(job_id), error=str(exc), stage="run_analysis_job")
        raise
    finally:
        db.close()


def recover_and_requeue_orphans() -> list[str]:
    """Periodic/worker-start hook: requeue orphaned processing jobs exactly once."""
    db = SessionLocal()
    try:
        recovered = recover_orphaned_jobs(db)
        db.commit()
        ids = [str(i) for i in recovered]
        if ids:
            from app.workers.queue import enqueue_analysis

            for rid in ids:
                enqueue_analysis(rid)
        return ids
    finally:
        db.close()


def cert_ping(n: int) -> int:
    """No-op used only by ops volume certification. Not a product API."""
    from redis import Redis

    from app.config import get_settings

    Redis.from_url(get_settings().redis_url, socket_timeout=2, protocol=2).incr("cert:ping:done")
    return int(n)


def record_poison_job(job_id: str, error: str) -> None:
    log.error("poison_analysis_job", job_id=job_id, error=error)
    from app.core.alerting import notify_worker_failure

    notify_worker_failure(job_id=str(job_id), error=error, stage="dead_letter")
    try:
        db = SessionLocal()
        try:
            fail_job(db, UUID(str(job_id)), "Analysis failed after repeated retries.")
            db.commit()
        finally:
            db.close()
    except Exception as exc:  # noqa: BLE001
        log.error("poison_job_mark_failed", job_id=job_id, error=str(exc), exc_info=exc)
