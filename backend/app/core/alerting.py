"""Minimal operational alerting — webhook (Slack/Discord-compatible) + optional file sink.

No Grafana/Prometheus required. Delivery is rate-limited per alert key.
"""

from __future__ import annotations

import json
import threading
import time
import traceback
from collections import defaultdict, deque
from pathlib import Path
from typing import Any
from urllib.error import URLError, HTTPError
from urllib.request import Request, urlopen

from app.core.logging import get_logger
from app.core.metrics import incr

log = get_logger("alerting")

_lock = threading.Lock()
_last_sent: dict[str, float] = {}
_burst_counts: dict[str, int] = defaultdict(int)
_five_xx: deque[float] = deque()

# Defaults; overridden by settings when available.
DEFAULT_THROTTLE_SECONDS = 120
DEFAULT_5XX_WINDOW_SECONDS = 60
DEFAULT_5XX_THRESHOLD = 5


def _settings():
    from app.config import get_settings

    return get_settings()


def fire_alert(
    alert_type: str,
    *,
    title: str,
    detail: str,
    severity: str = "warning",
    context: dict[str, Any] | None = None,
    force: bool = False,
) -> bool:
    """Send one alert if not throttled. Returns True if a notification was delivered."""
    settings = _settings()
    throttle = getattr(settings, "alert_throttle_seconds", DEFAULT_THROTTLE_SECONDS)
    key = f"{alert_type}:{title}"
    now = time.time()
    with _lock:
        last = _last_sent.get(key, 0.0)
        if not force and now - last < throttle:
            _burst_counts[key] += 1
            incr("alerts.throttled")
            log.info("alert_throttled", alert_type=alert_type, title=title, suppressed=_burst_counts[key])
            return False
        suppressed = _burst_counts.pop(key, 0)
        _last_sent[key] = now

    payload = {
        "alert_type": alert_type,
        "title": title,
        "detail": detail,
        "severity": severity,
        "suppressed_duplicates": suppressed,
        "context": context or {},
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "app": "AcademicCheck AI",
    }
    # Slack/Discord-friendly text field.
    text = (
        f"[{severity.upper()}] {title}\n{detail}\n"
        f"type={alert_type} suppressed={suppressed} at={payload['ts']}"
    )
    body = {**payload, "text": text, "content": text}

    delivered = False
    webhook = (getattr(settings, "alert_webhook_url", None) or "").strip()
    if webhook:
        delivered = _post_webhook(webhook, body) or delivered
    sink_file = (getattr(settings, "alert_sink_file", None) or "").strip()
    if sink_file:
        delivered = _append_sink(sink_file, body) or delivered
    pd_key = (getattr(settings, "pagerduty_routing_key", None) or "").strip()
    if pd_key:
        delivered = _post_pagerduty(pd_key, payload, severity=severity) or delivered
    if not webhook and not sink_file and not pd_key:
        # Always log — never silent when misconfigured.
        log.error("alert_no_destination", **{k: v for k, v in payload.items() if k != "context"})
        incr("alerts.undelivered")
        return False

    if delivered:
        incr("alerts.sent")
        log.warning("alert_sent", alert_type=alert_type, title=title, severity=severity, suppressed=suppressed)
    else:
        incr("alerts.delivery_failed")
        log.error("alert_delivery_failed", alert_type=alert_type, title=title)
    return delivered


def note_http_5xx(*, path: str = "", status_code: int = 500) -> None:
    """Record a 5xx and fire spike alert when threshold is crossed."""
    settings = _settings()
    window = getattr(settings, "alert_5xx_window_seconds", DEFAULT_5XX_WINDOW_SECONDS)
    threshold = getattr(settings, "alert_5xx_threshold", DEFAULT_5XX_THRESHOLD)
    now = time.time()
    with _lock:
        _five_xx.append(now)
        while _five_xx and now - _five_xx[0] > window:
            _five_xx.popleft()
        count = len(_five_xx)
    if count >= threshold:
        fire_alert(
            "http_5xx_spike",
            title=f"HTTP 5xx spike ({count} in {window}s)",
            detail=f"Latest status={status_code} path={path or 'unknown'}",
            severity="critical",
            context={"count": count, "window_seconds": window, "path": path, "status_code": status_code},
        )


def notify_unhandled_exception(*, path: str, error: str, stack: str, request_id: str | None = None) -> bool:
    return fire_alert(
        "unhandled_exception",
        title="Unhandled API exception",
        detail=error[:500],
        severity="critical",
        context={"path": path, "request_id": request_id, "stack": stack[:4000]},
    )


def notify_payment_failure(*, provider: str, reason: str, payment_id: str | None = None, event_id: str | None = None) -> bool:
    return fire_alert(
        "payment_failure",
        title=f"Payment/webhook failure ({provider})",
        detail=reason[:500],
        severity="critical",
        context={"provider": provider, "payment_id": payment_id, "event_id": event_id},
    )


def notify_worker_failure(*, job_id: str, error: str, stage: str = "worker") -> bool:
    return fire_alert(
        "worker_failure",
        title=f"Background job failure ({stage})",
        detail=error[:500],
        severity="critical",
        context={"job_id": job_id, "stage": stage},
    )


def notify_backup_failure(*, error: str, script: str = "backup_postgres.sh") -> bool:
    return fire_alert(
        "backup_failure",
        title="Scheduled backup failure",
        detail=error[:500],
        severity="critical",
        context={"script": script},
    )


def reset_alert_state_for_tests() -> None:
    with _lock:
        _last_sent.clear()
        _burst_counts.clear()
        _five_xx.clear()


def _post_webhook(url: str, body: dict) -> bool:
    data = json.dumps(body).encode("utf-8")
    req = Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urlopen(req, timeout=5) as resp:
            return 200 <= int(resp.status) < 300
    except (HTTPError, URLError, TimeoutError, OSError) as exc:
        log.error("alert_webhook_error", error=str(exc), url=url[:80])
        return False


def _post_pagerduty(routing_key: str, payload: dict, *, severity: str) -> bool:
    """Events API v2. Ready to activate when PAGERDUTY_ROUTING_KEY is set (HAL-11)."""
    sev = "critical" if severity in {"critical", "error"} else "warning" if severity == "warning" else "info"
    body = {
        "routing_key": routing_key,
        "event_action": "trigger",
        "dedup_key": f"{payload.get('alert_type')}:{payload.get('title')}"[:255],
        "payload": {
            "summary": f"[AcademicCheck] {payload.get('title')}",
            "severity": sev,
            "source": "academiccheck-api",
            "custom_details": {
                "detail": payload.get("detail"),
                "alert_type": payload.get("alert_type"),
                "context": payload.get("context") or {},
                "ts": payload.get("ts"),
            },
        },
    }
    return _post_webhook("https://events.pagerduty.com/v2/enqueue", body)


def _append_sink(path: str, body: dict) -> bool:
    try:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(body) + "\n")
        return True
    except OSError as exc:
        log.error("alert_sink_file_error", error=str(exc))
        return False


def format_exception(exc: BaseException) -> str:
    return "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
