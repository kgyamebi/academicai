"""Secret resolution abstraction.

Sources (first wins per key, after process env):
  1. Already-set environment variables (Railway / Render / Vercel / Doppler sync / Infisical sync)
  2. SECRETS_FILE JSON (K8s CSI / Secrets Store / Doppler download / Infisical export)
  3. SECRET_MANAGER_URI shape validation (CSI mount must still present SECRETS_FILE)

Supported SECRET_MANAGER_URI prefixes (operators sync JSON to SECRETS_FILE):
  aws-secretsmanager://  gcp-secretmanager://  vault://  file://
  doppler://  infisical://  railway://  render://

Pointing at a cloud secret manager is done by mounting or exporting the same JSON
shape — zero application code changes beyond this allow-list.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

_ALLOWED = {
    "JWT_SECRET_KEY",
    "JWT_SECRET_PREVIOUS",
    "APP_SECRET_KEY",
    "FIELD_ENCRYPTION_KEY",
    "DATABASE_URL",
    "REDIS_URL",
    "STRIPE_SECRET_KEY",
    "STRIPE_WEBHOOK_SECRET",
    "STRIPE_PUBLISHABLE_KEY",
    "PAYSTACK_SECRET_KEY",
    "PAYSTACK_WEBHOOK_SECRET",
    "FLUTTERWAVE_SECRET_KEY",
    "FLUTTERWAVE_WEBHOOK_HASH",
    "OPENAI_API_KEY",
    "ANTHROPIC_API_KEY",
    "GEMINI_API_KEY",
    "S3_ACCESS_KEY",
    "S3_SECRET_KEY",
    "SENTRY_DSN",
    "SMTP_PASSWORD",
    "EMAIL_API_KEY",
    "RESEND_API_KEY",
    "ALERT_WEBHOOK_URL",
    "PAGERDUTY_ROUTING_KEY",
    "PAGERDUTY_API_KEY",
    "BACKUP_ENCRYPTION_KEY",
    "BACKUP_ENCRYPTION_KEY_PREVIOUS",
    "FIELD_ENCRYPTION_KEY_PREVIOUS",
}

_URI_PREFIXES = (
    "aws-secretsmanager://",
    "gcp-secretmanager://",
    "vault://",
    "file://",
    "doppler://",
    "infisical://",
    "railway://",
    "render://",
)

_injected = False


def allowed_secret_keys() -> frozenset[str]:
    return frozenset(_ALLOWED)


def inject_secrets_file() -> None:
    """Load manager-mounted JSON into empty env slots. Idempotent."""
    global _injected
    if _injected:
        return
    uri = (os.environ.get("SECRET_MANAGER_URI") or "").strip()
    if uri and not uri.startswith(_URI_PREFIXES):
        raise RuntimeError(
            "SECRET_MANAGER_URI must use one of: "
            + ", ".join(_URI_PREFIXES)
            + " — and present secrets via SECRETS_FILE JSON (or process env)."
        )

    path = (os.environ.get("SECRETS_FILE") or "").strip()
    if uri.startswith("file://"):
        path = path or uri[len("file://") :]
    if not path:
        _injected = True
        return
    file = Path(path)
    if not file.is_file():
        raise RuntimeError("SECRETS_FILE is set but the file does not exist.")
    try:
        data = json.loads(file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise RuntimeError("SECRETS_FILE must contain a JSON object.") from exc
    if not isinstance(data, dict):
        raise RuntimeError("SECRETS_FILE must contain a JSON object.")
    for key, value in data.items():
        if key not in _ALLOWED:
            continue
        if os.environ.get(key):
            continue
        if value is None:
            continue
        os.environ[key] = str(value)
    _injected = True


def reset_secrets_injection() -> None:
    """Test helper only."""
    global _injected
    _injected = False
