from fastapi import APIRouter, Request, Response
from sqlalchemy import text

from app.config import get_settings
from app.core.logging import get_logger
from app.core.metrics import latency_snapshot, snapshot
from app.db.session import engine
from app.services.ai.circuit import snapshot as circuit_snapshot
from app.workers.queue import queue_depth, redis_client, registered_workers

log = get_logger("health")
router = APIRouter(tags=["health"])


@router.get("/api/live")
def live() -> dict:
    return {"status": "ok"}


@router.get("/api/health")
def health() -> dict:
    return _status(deep=False)


@router.get("/api/ready")
def ready(response: Response) -> dict:
    # Include queue metadata via cached registered_workers() (≤2s TTL in queue module).
    # Do not import RQ Worker helpers in this module — keep ready checks cheap.
    body = _status(deep=True, queue_meta=True)
    if not body["ready"]:
        response.status_code = 503
    return body


@router.get("/api/metrics")
def metrics() -> dict:
    from app.core.metrics import endpoint_snapshot, gauges_snapshot, refresh_runtime_gauges

    refresh_runtime_gauges()
    body = _status(deep=True, queue_meta=True)
    body["counters"] = snapshot()
    body["gauges"] = gauges_snapshot()
    body["endpoints"] = endpoint_snapshot()
    body["ai_circuits"] = circuit_snapshot()
    body["http_latency"] = latency_snapshot()
    return body


@router.get("/api/metrics/prometheus")
def prometheus_metrics() -> Response:
    """Prometheus text exposition of the existing process counters. Ops scrape surface only."""
    from app.core.metrics import endpoint_snapshot, gauges_snapshot, refresh_runtime_gauges

    refresh_runtime_gauges()
    counts = snapshot()
    latency = latency_snapshot()
    gauges = gauges_snapshot()
    endpoints = endpoint_snapshot()
    body = _status(deep=True, queue_meta=True)
    lines = [
        "# HELP academiccheck_ready 1 if /api/ready would pass",
        "# TYPE academiccheck_ready gauge",
        f"academiccheck_ready {1 if body.get('ready') else 0}",
        "# HELP academiccheck_database 1 if database ping succeeded",
        "# TYPE academiccheck_database gauge",
        f"academiccheck_database {1 if body.get('database') else 0}",
        "# HELP academiccheck_redis 1 if redis ping succeeded, -1 if not checked",
        "# TYPE academiccheck_redis gauge",
        f"academiccheck_redis {-1 if body.get('redis') is None else (1 if body.get('redis') else 0)}",
        "# HELP academiccheck_queue_depth RQ analysis queue length",
        "# TYPE academiccheck_queue_depth gauge",
        f"academiccheck_queue_depth {body.get('queue_depth') if body.get('queue_depth') is not None else -1}",
        "# HELP academiccheck_workers Registered RQ workers (cached 2s)",
        "# TYPE academiccheck_workers gauge",
        f"academiccheck_workers {body.get('workers') if body.get('workers') is not None else -1}",
        "# HELP academiccheck_http_latency_ms Rolling in-process latency",
        "# TYPE academiccheck_http_latency_ms gauge",
        f"academiccheck_http_latency_ms{{quantile=\"0.5\"}} {latency.get('p50_ms', 0)}",
        f"academiccheck_http_latency_ms{{quantile=\"0.95\"}} {latency.get('p95_ms', 0)}",
        f"academiccheck_http_latency_ms{{quantile=\"0.99\"}} {latency.get('p99_ms', 0)}",
        "# HELP academiccheck_http_latency_samples Rolling histogram sample count",
        "# TYPE academiccheck_http_latency_samples gauge",
        f"academiccheck_http_latency_samples {latency.get('n', 0)}",
    ]
    for name, value in sorted(counts.items()):
        if not name.startswith("email."):
            continue
        metric = "academiccheck_" + name.replace(".", "_").replace("-", "_")
        lines.append(f"# HELP {metric} Email delivery counter")
        lines.append(f"# TYPE {metric} counter")
        lines.append(f"{metric} {int(value)}")
    for name, value in sorted(gauges.items()):
        metric = "academiccheck_" + name.replace(".", "_").replace("-", "_")
        lines.append(f"# TYPE {metric} gauge")
        lines.append(f"{metric} {float(value)}")
    for path, stats in sorted(endpoints.items()):
        safe = path.replace('"', "").replace("\\", "")
        lines.append("# TYPE academiccheck_http_requests_total counter")
        lines.append(f'academiccheck_http_requests_total{{path="{safe}"}} {int(stats["requests"])}')
        lines.append("# TYPE academiccheck_http_errors_5xx_total counter")
        lines.append(f'academiccheck_http_errors_5xx_total{{path="{safe}"}} {int(stats["errors_5xx"])}')
        lines.append("# TYPE academiccheck_http_endpoint_p95_ms gauge")
        lines.append(f'academiccheck_http_endpoint_p95_ms{{path="{safe}"}} {float(stats["p95_ms"])}')
    for name, value in sorted(counts.items()):
        metric = "academiccheck_" + name.replace(".", "_").replace("-", "_")
        lines.append(f"# TYPE {metric} counter")
        lines.append(f"{metric} {int(value)}")
    circuits = circuit_snapshot()
    if circuits:
        lines.append("# HELP academiccheck_circuit 1 if named circuit is in this state")
        lines.append("# TYPE academiccheck_circuit gauge")
        for name, state in sorted(circuits.items()):
            safe = name.replace('"', "")
            lines.append(f'academiccheck_circuit{{name="{safe}",state="{state}"}} 1')
    return Response("\n".join(lines) + "\n", media_type="text/plain; version=0.0.4")


@router.post("/api/ops/sentry-probe")
def sentry_probe(request: Request) -> dict:
    """Emit a controlled exception to verify Sentry. Staging/dev only; gated by OPS_PROBE_TOKEN when set."""
    import os

    from fastapi import HTTPException

    from app.core.security import constant_time_equals

    settings = get_settings()
    if settings.app_env not in {"staging", "development"}:
        raise HTTPException(404, "Not found.")
    expected = (os.environ.get("OPS_PROBE_TOKEN") or "").strip()
    provided = (request.headers.get("x-ops-probe-token") or "").strip()
    if expected and not constant_time_equals(expected, provided):
        raise HTTPException(404, "Not found.")
    if not (settings.sentry_dsn or "").strip():
        return {"ok": False, "sentry_armed": False, "detail": "SENTRY_DSN is empty."}
    from app.core.sentry_bootstrap import capture_exception, init_sentry

    armed = init_sentry(service="api")
    capture_exception(RuntimeError("academiccheck_sentry_probe_intentional"), purpose="launch_validation")
    return {"ok": True, "sentry_armed": armed, "message": "Probe exception captured (check Sentry Issues)."}


@router.post("/api/ops/smtp-probe")
def smtp_probe(request: Request) -> dict:
    """Probe SMTP connectivity (and optional send). Staging/dev only; gated by OPS_PROBE_TOKEN."""
    import os

    from fastapi import HTTPException

    from app.core.security import constant_time_equals
    from app.services.emailer import assert_smtp_config, send_email_strict, smtp_status

    settings = get_settings()
    if settings.app_env not in {"staging", "development"}:
        raise HTTPException(404, "Not found.")
    expected = (os.environ.get("OPS_PROBE_TOKEN") or "").strip()
    provided = (request.headers.get("x-ops-probe-token") or "").strip()
    if expected and not constant_time_equals(expected, provided):
        raise HTTPException(404, "Not found.")

    status = smtp_status()
    if settings.email_provider != "smtp":
        return {"ok": False, "smtp": status, "detail": "EMAIL_PROVIDER is not smtp."}
    try:
        assert_smtp_config()
    except RuntimeError as exc:
        return {"ok": False, "smtp": status, "detail": str(exc)}

    if not status.get("ready"):
        return {"ok": False, "smtp": status, "detail": "SMTP probe (NOOP) failed."}

    to = (request.query_params.get("to") or "").strip()
    if to:
        send_email_strict(
            to,
            "AcademicCheck AI — SMTP probe",
            "SMTP probe succeeded. If you see this message, outbound delivery works.",
            html="<p>SMTP probe succeeded.</p>",
        )
        return {"ok": True, "smtp": status, "sent": True, "to_domain": to.split("@")[-1] if "@" in to else ""}
    return {"ok": True, "smtp": status, "sent": False}


def _storage_ok() -> bool:
    settings = get_settings()
    try:
        from pathlib import Path

        root = Path(settings.storage_local_path)
        root.mkdir(parents=True, exist_ok=True)
        probe = root / ".ready_probe"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink(missing_ok=True)
        return True
    except Exception as exc:  # noqa: BLE001
        log.debug("health_storage_check_failed", error=str(exc))
        return False


def _email_ok() -> bool:
    from app.services.emailer import smtp_delivery_ready

    settings = get_settings()
    if settings.email_provider == "console":
        return not (settings.is_production or settings.is_staging)
    return smtp_delivery_ready()


def _status(*, deep: bool, queue_meta: bool = False) -> dict:
    settings = get_settings()
    db_ok = True
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as exc:
        log.debug("health_db_check_failed", error=str(exc))
        db_ok = False
    redis_ok = None
    workers = None
    depth = None
    storage_ok = None
    email_ok = None
    if deep or settings.is_production or settings.is_staging:
        redis_ok = False
        try:
            client = redis_client()
            redis_ok = bool(client.ping())
            if redis_ok and queue_meta:
                workers = registered_workers()
                depth = queue_depth()
        except Exception as exc:
            log.debug("health_redis_check_failed", error=str(exc))
            redis_ok = False
        storage_ok = _storage_ok()
        email_ok = _email_ok()
    sqlite = settings.database_url.startswith("sqlite")
    ready = db_ok and not (settings.is_production and sqlite)
    strict_queue = settings.require_queue or settings.is_production or settings.is_staging
    if redis_ok is False and strict_queue:
        ready = False
    if strict_queue and redis_ok and queue_meta and (workers is None or workers < 1):
        ready = False
    if deep and storage_ok is False and (settings.is_production or settings.is_staging):
        ready = False
    if deep and email_ok is False and (settings.is_production or settings.is_staging):
        ready = False
    status = "ok" if ready else "degraded"
    return {
        "status": status,
        "service": settings.app_name,
        "database": db_ok,
        "redis": redis_ok,
        "workers": workers,
        "queue_depth": depth,
        "storage": storage_ok,
        "email": email_ok,
        "queue_required": strict_queue,
        "sqlite": sqlite,
        "ready": ready,
        "env": settings.app_env,
    }
