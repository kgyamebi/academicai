from app.config import get_settings
from app.core.logging import get_logger

log = get_logger("queue")


def enqueue_analysis(job_id: str) -> bool:
    settings = get_settings()
    try:
        from redis import Redis
        from rq import Queue

        redis = Redis.from_url(settings.redis_url)
        redis.ping()
        from rq import Worker

        if not Worker.all(connection=redis):
            log.warning("queue_has_no_workers_inline_fallback")
            return False
        queue = Queue("analysis", connection=redis)
        queue.enqueue("app.workers.tasks.run_analysis_job", job_id, job_timeout=600)
        return True
    except Exception as exc:  # noqa: BLE001
        log.warning("queue_unavailable_inline_fallback", error=str(exc))
        return False
