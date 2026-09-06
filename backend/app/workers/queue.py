from app.config import get_settings
from app.core.logging import get_logger

log = get_logger("queue")


def enqueue_analysis(job_id: str) -> bool:
    settings = get_settings()
    try:
        from redis import Redis
        from rq import Queue, Retry
        from rq import Worker

        redis = Redis.from_url(settings.redis_url, socket_timeout=2)
        redis.ping()
        if not Worker.all(connection=redis):
            log.warning("queue_has_no_workers")
            return False
        queue = Queue("analysis", connection=redis)
        dlq = Queue("analysis_dlq", connection=redis)
        queue.enqueue(
            "app.workers.tasks.run_analysis_job",
            job_id,
            job_timeout=600,
            retry=Retry(max=3, interval=[15, 60, 180]),
            on_failure=_on_failure,
            meta={"dlq": dlq.name},
        )
        return True
    except Exception as exc:  # noqa: BLE001
        log.warning("queue_unavailable", error=str(exc))
        return False


def _on_failure(job, connection, type, value, traceback):  # noqa: A002
    from rq import Queue

    dlq = Queue("analysis_dlq", connection=connection)
    dlq.enqueue("app.workers.tasks.record_poison_job", job.id, str(value), job_timeout=60)
    log.error("analysis_job_dead_letter", job_id=str(job.id), error=str(value))
