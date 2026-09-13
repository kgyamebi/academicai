import os
import signal

from redis import Redis
from rq import SimpleWorker, Worker

from app.config import get_settings
from app.core.logging import get_logger

log = get_logger("rq_worker")


def main() -> None:
    settings = get_settings()
    try:
        from app.core.sentry_bootstrap import init_sentry

        init_sentry(service="worker")
    except Exception as exc:  # noqa: BLE001
        log.debug("sentry_worker_skip", error=str(exc))
    redis = Redis.from_url(
        settings.redis_url,
        socket_timeout=5,
        socket_connect_timeout=5,
        protocol=2,
    )
    # RQ 2.x forks a work-horse; Windows has no os.fork().
    worker_cls = SimpleWorker if os.name == "nt" else Worker
    worker = worker_cls(["extract", "analysis", "email"], connection=redis)

    try:
        from app.workers.tasks import recover_and_requeue_orphans

        recovered = recover_and_requeue_orphans()
        if recovered:
            log.warning("worker_startup_recovered_jobs", count=len(recovered), job_ids=recovered)
    except Exception as exc:  # noqa: BLE001
        log.error("worker_startup_recovery_failed", error=str(exc), exc_info=exc)

    def _graceful(_signum, _frame) -> None:
        stop = getattr(worker, "request_stop", None)
        if callable(stop):
            stop()

    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            signal.signal(sig, _graceful)
        except Exception as exc:  # noqa: BLE001
            log.debug("signal_handler_unavailable", signal=str(sig), error=str(exc))
    worker.work()


if __name__ == "__main__":
    main()
