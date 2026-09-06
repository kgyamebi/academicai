from fastapi import APIRouter
from redis import Redis
from sqlalchemy import text

from app.config import get_settings
from app.core.metrics import snapshot
from app.db.session import engine

router = APIRouter(tags=["health"])


@router.get("/api/live")
def live() -> dict:
    return {"status": "ok"}


@router.get("/api/health")
def health() -> dict:
    return _status(deep=False)


@router.get("/api/ready")
def ready() -> dict:
    body = _status(deep=True)
    return body


@router.get("/api/metrics")
def metrics() -> dict:
    body = _status(deep=True)
    body["counters"] = snapshot()
    return body


def _status(*, deep: bool) -> dict:
    settings = get_settings()
    db_ok = True
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception:
        db_ok = False
    redis_ok = None
    workers = None
    if deep or settings.is_production:
        redis_ok = False
        try:
            client = Redis.from_url(settings.redis_url, socket_timeout=1)
            redis_ok = bool(client.ping())
            if redis_ok:
                from rq import Worker

                workers = len(Worker.all(connection=client))
        except Exception:
            redis_ok = False
    sqlite = settings.database_url.startswith("sqlite")
    ready = db_ok and not (settings.is_production and sqlite)
    if redis_ok is False and (settings.is_production or settings.require_queue):
        ready = False
    status = "ok" if ready else "degraded"
    return {
        "status": status,
        "service": settings.app_name,
        "database": db_ok,
        "redis": redis_ok,
        "workers": workers,
        "sqlite": sqlite,
        "ready": ready,
        "env": settings.app_env,
    }
