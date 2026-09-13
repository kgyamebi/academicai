"""Report whether live payment provider keys are present. Does not print secrets."""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
os.environ.setdefault("APP_ENV", "test")

from app.config import get_settings  # noqa: E402


def present(value: str) -> bool:
    return bool((value or "").strip())


def main() -> int:
    settings = get_settings()
    payload = {
        "measured_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "live_charges_executed": False,
        "providers": {
            "stripe": {
                "secret_present": present(settings.stripe_secret_key),
                "webhook_secret_present": present(settings.stripe_webhook_secret),
            },
            "paystack": {
                "secret_present": present(settings.paystack_secret_key),
                "webhook_secret_present": present(settings.paystack_webhook_secret),
            },
            "flutterwave": {
                "secret_present": present(settings.flutterwave_secret_key),
                "webhook_hash_present": present(settings.flutterwave_webhook_hash),
            },
        },
    }
    any_key = any(
        v
        for provider in payload["providers"].values()
        for v in provider.values()
    )
    payload["any_provider_key"] = any_key
    payload["live_certification"] = "blocked_no_provider_keys" if not any_key else "keys_present_charges_not_run"
    out = ROOT / "ops" / "cert_payment_keys.json"
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
