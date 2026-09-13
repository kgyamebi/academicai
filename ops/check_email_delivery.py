#!/usr/bin/env python3
"""Launch check: SMTP config + optional live probe.

Usage (from repo root, with backend venv + env loaded):
  python ops/check_email_delivery.py
  python ops/check_email_delivery.py --send you@yourdomain.com
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate email delivery readiness")
    parser.add_argument("--send", metavar="EMAIL", help="Send a probe message via send_email_strict")
    args = parser.parse_args()

    from app.config import get_settings
    from app.services.emailer import assert_smtp_config, get_email_provider, send_email_strict, smtp_delivery_ready, smtp_status

    settings = get_settings()
    status = smtp_status()
    print(f"APP_ENV={settings.app_env}")
    print(f"EMAIL_PROVIDER={settings.email_provider}")
    print(f"EMAIL_FROM={settings.email_from}")
    if settings.email_provider == "resend":
        print(f"EMAIL_API_KEY={'SET' if settings.resend_key else '(empty)'}")
    else:
        print(f"SMTP_HOST={settings.smtp_host or '(empty)'}")
        print(f"SMTP_PORT={settings.smtp_port}")
        print(f"SMTP_TLS={settings.smtp_tls}")
    print(f"status={status}")

    try:
        assert_smtp_config()
        print("assert_smtp_config: OK")
    except Exception as exc:  # noqa: BLE001
        print(f"assert_smtp_config: FAIL ({exc})")
        if settings.email_provider == "smtp":
            return 2

    if settings.email_provider == "console":
        if settings.is_production:
            print("FAIL: console provider is not allowed in production")
            return 3
        print("WARN: console provider — mail is printed to logs, not delivered")
        print("Tip: run `python ops/local_smtp_sink.py` then set EMAIL_PROVIDER=smtp SMTP_HOST=127.0.0.1 SMTP_PORT=1025 SMTP_TLS=disabled")
        return 0

    ready = smtp_delivery_ready()
    print(f"smtp_delivery_ready: {'OK' if ready else 'FAIL'}")
    if not ready:
        return 4

    if args.send:
        send_email_strict(
            args.send,
            "AcademicCheck AI — SMTP probe",
            "This is a delivery probe from ops/check_email_delivery.py. If you received it, SMTP works.",
            html="<p>This is a delivery probe from <code>ops/check_email_delivery.py</code>.</p>",
        )
        print(f"probe sent to {args.send}")

    provider = get_email_provider()
    print(f"provider={type(provider).__name__}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
