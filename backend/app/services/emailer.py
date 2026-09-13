"""Outbound email delivery — console (dev) or SMTP (launch/production).

Infrastructure: TLS modes, envelope sender, EHLO hostname, deliverability headers,
retries, circuit breaker, metrics, cached readiness probe, and RQ email queue with
sync fallback. Console is refused in production/staging launch gates.
"""

from __future__ import annotations

import re
import smtplib
import ssl
import time
import uuid
from email.message import EmailMessage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr, formatdate, make_msgid, parseaddr
from threading import Lock

from app.config import get_settings
from app.core.logging import get_logger
from app.core.metrics import incr, observe_ms
from app.services.ai.circuit import allow, record_failure, record_success

log = get_logger("email")

_probe_lock = Lock()
_probe_cache: tuple[float, bool] | None = None
_PROBE_TTL_SECONDS = 45.0


class EmailProvider:
    def send(self, to: str, subject: str, body: str, html: str | None = None) -> None:
        raise NotImplementedError

    def probe(self) -> bool:
        return True


def _redact_secrets(body: str) -> str:
    text = re.sub(r"(token=)[^&\s]+", r"\1[REDACTED]", body or "")
    text = re.sub(r"eyJ[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+", "[REDACTED]", text)
    text = re.sub(r"sk_(live|test)_[A-Za-z0-9]+", "[REDACTED]", text)
    return text


def _parsed_from_addr() -> tuple[str, str]:
    settings = get_settings()
    name, addr = parseaddr(settings.email_from)
    if not addr and "@" in (settings.email_from or ""):
        addr = settings.email_from.strip()
    return name or settings.app_name, addr or settings.email_from


def _envelope_from() -> str:
    settings = get_settings()
    if settings.email_envelope_from.strip():
        return settings.email_envelope_from.strip()
    return _parsed_from_addr()[1]


def _from_header() -> str:
    name, addr = _parsed_from_addr()
    return formataddr((name, addr))


def _apply_common_headers(msg: EmailMessage | MIMEMultipart) -> None:
    settings = get_settings()
    origin = settings.app_web_url.rstrip("/")
    unsub_url = f"{origin}/contact"
    mailto = settings.email_reply_to.strip() or _envelope_from()
    msg["X-Entity-Ref-ID"] = uuid.uuid4().hex
    msg["X-Auto-Response-Suppress"] = "All"
    msg["Auto-Submitted"] = "auto-generated"
    msg["List-Unsubscribe"] = f"<{unsub_url}>, <mailto:{mailto}?subject=unsubscribe>"
    msg["List-Unsubscribe-Post"] = "List-Unsubscribe=One-Click"
    if settings.email_reply_to.strip():
        msg["Reply-To"] = settings.email_reply_to.strip()


def _build_message(*, to: str, subject: str, body: str, html: str | None) -> EmailMessage | MIMEMultipart:
    settings = get_settings()
    _, addr = _parsed_from_addr()
    domain = addr.rsplit("@", 1)[-1] if "@" in addr else "academiccheck.local"

    if html:
        msg: EmailMessage | MIMEMultipart = MIMEMultipart("alternative")
        msg["From"] = _from_header()
        msg["To"] = to
        msg["Subject"] = subject
        msg["Date"] = formatdate(localtime=True)
        msg["Message-ID"] = make_msgid(domain=domain)
        msg["MIME-Version"] = "1.0"
        _apply_common_headers(msg)
        msg.attach(MIMEText(body, "plain", "utf-8"))
        msg.attach(MIMEText(html, "html", "utf-8"))
        return msg

    msg = EmailMessage()
    msg["From"] = _from_header()
    msg["To"] = to
    msg["Subject"] = subject
    msg["Date"] = formatdate(localtime=True)
    msg["Message-ID"] = make_msgid(domain=domain)
    _apply_common_headers(msg)
    msg.set_content(body)
    return msg


class ConsoleEmailProvider(EmailProvider):
    def send(self, to: str, subject: str, body: str, html: str | None = None) -> None:
        settings = get_settings()
        if settings.is_production:
            log.error("email_console_refused_in_production")
            raise RuntimeError("Console email is not allowed in production.")
        log.info("email_console", subject=subject, to_domain=to.split("@")[-1] if "@" in to else "")
        extra = f"\n[html:{len(html)} chars]" if html else ""
        print(f"\n--- EMAIL to [redacted] ---\n{subject}\n{_redact_secrets(body)}{extra}\n--- END EMAIL ---\n")


class SMTPEmailProvider(EmailProvider):
    def probe(self) -> bool:
        settings = get_settings()
        if not settings.smtp_host:
            return False
        try:
            self._connect_and(lambda smtp: smtp.noop())
            return True
        except Exception as exc:  # noqa: BLE001
            log.warning("smtp_probe_failed", error=str(exc))
            return False

    def send(self, to: str, subject: str, body: str, html: str | None = None) -> None:
        msg = _build_message(to=to, subject=subject, body=body, html=html)
        envelope = _envelope_from()
        last_exc: Exception | None = None
        for attempt in range(1, 4):
            try:
                self._connect_and(
                    lambda smtp: smtp.send_message(msg, from_addr=envelope, to_addrs=[to])
                )
                return
            except Exception as exc:  # noqa: BLE001
                last_exc = exc
                log.warning("smtp_send_retry", attempt=attempt, error=str(exc))
                time.sleep(0.4 * attempt)
        assert last_exc is not None
        raise last_exc

    def _tls_mode(self) -> str:
        settings = get_settings()
        mode = (settings.smtp_tls or "auto").lower()
        port = int(settings.smtp_port or 587)
        if mode == "auto":
            if port == 465:
                return "ssl"
            return "starttls"
        if mode == "required":
            return "ssl" if port == 465 else "starttls"
        if mode == "starttls":
            return "starttls"
        if mode == "disabled":
            if settings.is_production:
                raise RuntimeError("SMTP_TLS=disabled is not allowed in production.")
            return "plain"
        raise RuntimeError(f"Unknown SMTP_TLS mode: {mode}")

    def _login(self, smtp: smtplib.SMTP) -> None:
        settings = get_settings()
        need_auth = bool(settings.smtp_user) or settings.smtp_require_auth or settings.is_production
        if need_auth:
            if not settings.smtp_user or not settings.smtp_password:
                raise RuntimeError("SMTP authentication required but SMTP_USER/SMTP_PASSWORD are empty.")
            smtp.login(settings.smtp_user, settings.smtp_password)
        elif settings.smtp_user:
            smtp.login(settings.smtp_user, settings.smtp_password)

    def _local_hostname(self) -> str | None:
        host = (get_settings().smtp_ehlo_hostname or "").strip()
        return host or None

    def _connect_and(self, action) -> None:
        settings = get_settings()
        host = settings.smtp_host
        port = int(settings.smtp_port or 587)
        timeout = max(3, int(settings.smtp_timeout_seconds or 15))
        mode = self._tls_mode()
        context = ssl.create_default_context()
        local_hostname = self._local_hostname()
        ssl_kwargs = {"local_hostname": local_hostname} if local_hostname else {}

        if mode == "ssl":
            with smtplib.SMTP_SSL(host, port, timeout=timeout, context=context, **ssl_kwargs) as smtp:
                self._login(smtp)
                action(smtp)
            return

        with smtplib.SMTP(host, port, timeout=timeout, **ssl_kwargs) as smtp:
            smtp.ehlo()
            if mode == "starttls":
                try:
                    smtp.starttls(context=context)
                    smtp.ehlo()
                except smtplib.SMTPNotSupportedError as exc:
                    if settings.is_production or settings.is_staging or settings.smtp_tls in {"required", "starttls"}:
                        raise RuntimeError(
                            f"SMTP server {host}:{port} does not support STARTTLS (required)."
                        ) from exc
                    log.warning("smtp_starttls_unsupported", host=host, port=port)
            self._login(smtp)
            action(smtp)


class ResendEmailProvider(EmailProvider):
    """Invoice App pattern: HTTPS API to api.resend.com (not SMTP)."""

    def _headers(self) -> dict[str, str]:
        key = get_settings().resend_key
        if not key:
            raise RuntimeError("EMAIL_API_KEY / RESEND_API_KEY is empty.")
        return {
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        }

    def probe(self) -> bool:
        try:
            import httpx

            timeout = max(3, int(get_settings().smtp_timeout_seconds or 15))
            with httpx.Client(timeout=timeout) as client:
                response = client.get("https://api.resend.com/domains", headers=self._headers())
            if response.status_code in {200, 401, 403}:
                # 401/403 still prove reachability + key format path; treat 200 as ready.
                return response.status_code == 200
            log.warning("resend_probe_unexpected", status=response.status_code)
            return False
        except Exception as exc:  # noqa: BLE001
            log.warning("resend_probe_failed", error=str(exc))
            return False

    def send(self, to: str, subject: str, body: str, html: str | None = None) -> None:
        import httpx

        settings = get_settings()
        timeout = max(3, int(settings.smtp_timeout_seconds or 15))
        payload: dict = {
            "from": settings.email_from,
            "to": [to],
            "subject": subject,
            "text": body,
        }
        if html:
            payload["html"] = html
        if settings.email_reply_to.strip():
            payload["reply_to"] = settings.email_reply_to.strip()
        last_exc: Exception | None = None
        for attempt in range(1, 4):
            try:
                with httpx.Client(timeout=timeout) as client:
                    response = client.post(
                        "https://api.resend.com/emails",
                        headers=self._headers(),
                        json=payload,
                    )
                if response.status_code >= 400:
                    detail = (response.text or "")[:400]
                    raise RuntimeError(f"Resend HTTP {response.status_code}: {detail}")
                return
            except Exception as exc:  # noqa: BLE001
                last_exc = exc
                log.warning("resend_send_retry", attempt=attempt, error=str(exc))
                time.sleep(0.4 * attempt)
        assert last_exc is not None
        raise last_exc


def get_email_provider() -> EmailProvider:
    settings = get_settings()
    if settings.email_provider == "smtp":
        if not settings.smtp_host.strip():
            raise RuntimeError("EMAIL_PROVIDER=smtp requires SMTP_HOST.")
        return SMTPEmailProvider()
    if settings.email_provider == "resend":
        if not settings.resend_key:
            raise RuntimeError("EMAIL_PROVIDER=resend requires EMAIL_API_KEY or RESEND_API_KEY.")
        return ResendEmailProvider()
    return ConsoleEmailProvider()


def assert_smtp_config() -> None:
    """Fail fast when outbound email provider is incomplete (SMTP or Resend)."""
    settings = get_settings()
    if settings.email_provider == "console":
        return
    missing = []
    if not settings.email_from.strip() or "@" not in settings.email_from:
        missing.append("EMAIL_FROM")
    if settings.email_provider == "smtp":
        if not settings.smtp_host.strip():
            missing.append("SMTP_HOST")
        if settings.is_production and settings.smtp_tls == "disabled":
            missing.append("SMTP_TLS(not disabled)")
        if (settings.is_production or settings.smtp_require_auth) and (
            not settings.smtp_user.strip() or not settings.smtp_password
        ):
            missing.append("SMTP_USER/SMTP_PASSWORD")
    elif settings.email_provider == "resend":
        if not settings.resend_key:
            missing.append("EMAIL_API_KEY")
    if missing:
        raise RuntimeError(f"Email misconfigured; set: {', '.join(missing)}")


def invalidate_smtp_probe_cache() -> None:
    global _probe_cache
    with _probe_lock:
        _probe_cache = None


def smtp_delivery_ready(*, force: bool = False) -> bool:
    settings = get_settings()
    if settings.email_provider == "console":
        return settings.app_env not in {"production", "staging"}
    if settings.email_provider not in {"smtp", "resend"}:
        return False
    try:
        assert_smtp_config()
    except RuntimeError:
        return False

    global _probe_cache
    now = time.monotonic()
    with _probe_lock:
        if not force and _probe_cache and now - _probe_cache[0] < _PROBE_TTL_SECONDS:
            return _probe_cache[1]
    try:
        ok = get_email_provider().probe()
    except Exception:  # noqa: BLE001
        ok = False
    with _probe_lock:
        _probe_cache = (now, ok)
    return ok


def smtp_status() -> dict:
    settings = get_settings()
    try:
        provider_name = type(get_email_provider()).__name__
    except Exception as exc:  # noqa: BLE001
        provider_name = f"error:{exc}"
    return {
        "provider": settings.email_provider,
        "host": settings.smtp_host or None,
        "port": settings.smtp_port if settings.email_provider == "smtp" else None,
        "tls": settings.smtp_tls if settings.email_provider == "smtp" else None,
        "resend_configured": bool(settings.resend_key) if settings.email_provider == "resend" else None,
        "from": settings.email_from,
        "envelope_from": _envelope_from() if settings.email_provider == "smtp" else None,
        "reply_to": settings.email_reply_to or None,
        "async": settings.email_async,
        "ready": smtp_delivery_ready(),
        "implementation": provider_name,
    }


def deliver_email_now(to: str, subject: str, body: str, html: str | None = None) -> None:
    """Synchronous send used by the worker and probes. Raises on hard failure."""
    settings = get_settings()
    started = time.perf_counter()
    provider = get_email_provider()
    circuit_name = None
    if isinstance(provider, SMTPEmailProvider):
        circuit_name = "smtp"
    elif isinstance(provider, ResendEmailProvider):
        circuit_name = "resend"
    if circuit_name and not allow(circuit_name):
        incr("email.circuit_open")
        _alert_send_failure(subject, f"{circuit_name} circuit open")
        raise RuntimeError(f"{circuit_name} circuit is open.")
    try:
        provider.send(to, subject, body, html=html)
        if circuit_name:
            record_success(circuit_name)
        incr("email.sent")
        observe_ms((time.perf_counter() - started) * 1000)
        log.info("email_sent", subject=subject, provider=settings.email_provider)
    except Exception as exc:
        if circuit_name:
            record_failure(circuit_name)
        incr("email.failed")
        log.error("email_send_failed", subject=subject, error=str(exc))
        _alert_send_failure(subject, str(exc))
        raise


def send_email(to: str, subject: str, body: str, html: str | None = None) -> None:
    """Product send: prefer RQ email queue, sync fallback. Never raises to callers."""
    settings = get_settings()
    if settings.email_async:
        try:
            from app.workers.queue import enqueue_email

            if enqueue_email(to, subject, body, html):
                incr("email.queued")
                log.info("email_queued", subject=subject)
                return
        except Exception as exc:  # noqa: BLE001
            log.warning("email_enqueue_failed", error=str(exc))
            incr("email.enqueue_fallback")
    try:
        deliver_email_now(to, subject, body, html=html)
    except Exception:  # noqa: BLE001
        # Already logged/alerted in deliver_email_now
        pass


def send_email_strict(to: str, subject: str, body: str, html: str | None = None) -> None:
    """Sync send that raises (ops probes). Bypasses the queue."""
    deliver_email_now(to, subject, body, html=html)


def _alert_send_failure(subject: str, error: str) -> None:
    try:
        from app.core.alerting import fire_alert

        fire_alert(
            "email_send_failed",
            title="Outbound email failed",
            detail=f"{subject}: {error[:400]}",
            severity="critical",
        )
    except Exception:  # noqa: BLE001
        pass
