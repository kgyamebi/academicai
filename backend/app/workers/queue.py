from threading import Lock
import time

from app.config import get_settings
from app.core.logging import get_logger

log = get_logger("queue")
_lock = Lock()
_redis = None
_workers_cache: tuple[float, int] | None = None


def redis_client():
    global _redis
    settings = get_settings()
    with _lock:
        if _redis is None:
            from redis import Redis

            # protocol=2: compatible with Redis 5.x (HELLO/RESP3 unsupported on older servers).
            _redis = Redis.from_url(
                settings.redis_url,
                socket_timeout=2,
                socket_connect_timeout=2,
                max_connections=64,
                protocol=2,
            )
        return _redis


def reset_redis_client() -> None:
    global _redis, _workers_cache
    with _lock:
        _redis = None
        _workers_cache = None


def registered_workers() -> int:
    """Cached RQ worker count. Ready checks must not call this on every request."""
    global _workers_cache
    now = time.monotonic()
    with _lock:
        if _workers_cache and now - _workers_cache[0] < 2.0:
            return _workers_cache[1]
    try:
        from rq import Worker

        n = len(Worker.all(connection=redis_client()))
    except Exception as exc:  # noqa: BLE001
        log.warning("worker_count_unavailable", error=str(exc))
        n = 0
    with _lock:
        _workers_cache = (now, n)
    return n


def queue_depth() -> int:
    try:
        redis = redis_client()
        for key in ("rq:queue:analysis", "rq:queues:analysis"):
            depth = redis.llen(key)
            if depth:
                return int(depth)
        return int(redis.llen("rq:queue:analysis") or 0)
    except Exception as exc:  # noqa: BLE001
        log.warning("queue_depth_unavailable", error=str(exc))
        return -1


def enqueue_extract(document_id: str) -> bool:
    """Queue PDF/DOCX extraction. Returns False if Redis is unavailable."""
    try:
        from rq import Queue, Retry, Worker
        from rq.exceptions import DuplicateJobError

        redis = redis_client()
        redis.ping()
        if not Worker.all(connection=redis):
            log.warning("extract_queue_has_no_workers")
            return False
        queue = Queue("extract", connection=redis)
        rq_id = f"extract-{document_id}"
        existing = queue.fetch_job(rq_id)
        if existing is not None:
            status = existing.get_status()
            if status in {"queued", "started", "deferred", "scheduled"}:
                return True
            existing.delete()
        queue.enqueue(
            "app.workers.tasks.run_extract_job",
            document_id,
            job_id=rq_id,
            job_timeout=300,
            retry=Retry(max=2, interval=[10, 30]),
        )
        return True
    except DuplicateJobError:
        return True
    except Exception as exc:  # noqa: BLE001
        log.warning("extract_queue_unavailable", error=str(exc))
        return False


def enqueue_email(to: str, subject: str, body: str, html: str | None = None) -> bool:
    """Queue outbound mail on the dedicated email RQ queue. Returns False if unavailable."""
    try:
        from rq import Queue, Retry, Worker

        redis = redis_client()
        redis.ping()
        if not Worker.all(connection=redis):
            log.warning("email_queue_has_no_workers")
            return False
        queue = Queue("email", connection=redis)
        queue.enqueue(
            "app.workers.tasks.run_send_email",
            to,
            subject,
            body,
            html,
            job_timeout=120,
            retry=Retry(max=4, interval=[5, 15, 45, 120]),
            failure_ttl=86400,
            result_ttl=3600,
        )
        return True
    except Exception as exc:  # noqa: BLE001
        log.warning("email_queue_unavailable", error=str(exc))
        return False


def enqueue_analysis(job_id: str) -> bool:
    try:
        from rq import Queue, Retry, Worker
        from rq.exceptions import DuplicateJobError

        redis = redis_client()
        redis.ping()
        if not Worker.all(connection=redis):
            log.warning("queue_has_no_workers")
            return False
        queue = Queue("analysis", connection=redis)
        if _job_already_terminal(job_id):
            return True
        existing = queue.fetch_job(job_id)
        if existing is not None:
            status = existing.get_status()
            if status in {"queued", "started", "deferred", "scheduled"}:
                return True
            existing.delete()
        queue.enqueue(
            "app.workers.tasks.run_analysis_job",
            job_id,
            job_id=job_id,
            job_timeout=600,
            retry=Retry(max=3, interval=_retry_intervals_with_jitter()),
            on_failure=_on_failure,
            meta={"dlq": "analysis_dlq"},
        )
        return True
    except DuplicateJobError:
        return True
    except Exception as exc:  # noqa: BLE001
        log.warning("queue_unavailable", error=str(exc))
        return False


def _retry_intervals_with_jitter() -> list[int]:
    """Stepped backoff with jitter so crashed workers do not retry in lockstep."""
    import random

    return [15 + random.randint(0, 5), 60 + random.randint(0, 15), 180 + random.randint(0, 30)]


def _job_already_terminal(job_id: str) -> bool:
    try:
        from uuid import UUID

        from app.db.session import SessionLocal
        from app.models.analysis import AnalysisJob

        db = SessionLocal()
        try:
            job = db.get(AnalysisJob, UUID(job_id))
            return bool(job and job.status in {"completed", "cancelled", "failed"})
        finally:
            db.close()
    except Exception as exc:  # noqa: BLE001
        log.warning("terminal_job_lookup_failed", job_id=job_id, error=str(exc))
        return False


def _on_failure(job, connection, type, value, traceback):  # noqa: A002
    from rq import Queue

    from app.core.metrics import incr
    from app.workers.tasks import record_poison_job

    incr("jobs.dead_letter")
    dlq = Queue("analysis_dlq", connection=connection)
    dlq.enqueue("app.workers.tasks.record_poison_job", job.id, str(value), job_timeout=60)
    record_poison_job(str(job.id), str(value))
    log.error("analysis_job_dead_letter", job_id=str(job.id), error=str(value))
