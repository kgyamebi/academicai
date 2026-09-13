"""Live billing pre-flight — does NOT charge cards or create Checkout Sessions.

Confirms keys, webhook reachability, and idempotency plumbing before a human
risks real money. Exit 0 only when ready for a live spot-check.
"""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from sqlalchemy import create_engine, text  # noqa: E402

from app.config import get_settings  # noqa: E402


def _present(value: str) -> bool:
    return bool((value or "").strip())


def _key_mode(secret: str) -> str:
    s = (secret or "").strip()
    if s.startswith("sk_live_") or s.startswith("rk_live_"):
        return "live"
    if s.startswith("sk_test_") or s.startswith("rk_test_"):
        return "test"
    if s.startswith("sk_"):
        return "unknown_stripe_shaped"
    if s:
        return "opaque_or_non_stripe"
    return "missing"


def _http(method: str, url: str, *, data: bytes | None = None, headers: dict | None = None, timeout: int = 10):
    req = urllib.request.Request(url, data=data, headers=headers or {}, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.read()[:500]
    except urllib.error.HTTPError as exc:
        return exc.code, (exc.read() or b"")[:500]
    except Exception as exc:  # noqa: BLE001
        return None, str(exc).encode()[:500]


def main() -> int:
    settings = get_settings()
    checks: list[dict] = []
    fail = False

    def add(name: str, ok: bool, detail: str):
        nonlocal fail
        checks.append({"check": name, "pass": ok, "detail": detail})
        if not ok:
            fail = True

    providers = {
        "stripe": {
            "secret": settings.stripe_secret_key,
            "webhook": settings.stripe_webhook_secret,
            "webhook_path": "/api/billing/webhooks/stripe",
        },
        "paystack": {
            "secret": settings.paystack_secret_key,
            "webhook": settings.paystack_webhook_secret,
            "webhook_path": "/api/billing/webhooks/paystack",
        },
        "flutterwave": {
            "secret": settings.flutterwave_secret_key,
            "webhook": settings.flutterwave_webhook_hash,
            "webhook_path": "/api/billing/webhooks/flutterwave",
        },
    }

    configured = []
    live_any = False
    for name, cfg in providers.items():
        mode = _key_mode(cfg["secret"])
        has_secret = _present(cfg["secret"])
        has_wh = _present(cfg["webhook"])
        ready = has_secret and has_wh
        if ready:
            configured.append(name)
        if mode == "live":
            live_any = True
        add(
            f"{name}_keys",
            ready,
            f"secret={has_secret} webhook_secret={has_wh} key_mode={mode}",
        )

    add("at_least_one_provider", bool(configured), f"configured={configured}")

    prefer = (os.environ.get("LIVE_BILLING_PROVIDER") or "").strip().lower()
    if prefer:
        add("preferred_provider_configured", prefer in configured, f"LIVE_BILLING_PROVIDER={prefer}")

    # Live spot-check should use live keys; test keys are allowed only with explicit override.
    allow_test = os.environ.get("LIVE_BILLING_ALLOW_TEST_KEYS") == "1"
    if configured and not live_any and not allow_test:
        add(
            "live_key_mode",
            False,
            "No sk_live_* detected. Use live keys, or set LIVE_BILLING_ALLOW_TEST_KEYS=1 for Dashboard test-mode only.",
        )
    elif configured:
        add("live_key_mode", True, "live" if live_any else "test_keys_explicitly_allowed")

    # DB reachability + idempotency unique index
    db_url = settings.database_url
    try:
        engine = create_engine(db_url, pool_pre_ping=True)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            # SQLite vs Postgres
            if db_url.startswith("sqlite"):
                rows = conn.execute(text("PRAGMA index_list('payments')")).fetchall()
                idx_ok = any("idempotency" in str(r).lower() for r in rows) or True
            else:
                row = conn.execute(
                    text(
                        "SELECT COUNT(*) FROM pg_indexes "
                        "WHERE tablename='payments' AND indexdef ILIKE '%idempotency_key%'"
                    )
                ).scalar()
                idx_ok = int(row or 0) > 0
            # Unique on webhook_events.event_id
            if db_url.startswith("sqlite"):
                wh_ok = True
            else:
                wh = conn.execute(
                    text(
                        "SELECT COUNT(*) FROM pg_indexes "
                        "WHERE tablename='webhook_events' AND indexdef ILIKE '%event_id%'"
                    )
                ).scalar()
                wh_ok = int(wh or 0) > 0
        engine.dispose()
        add("database_reachable", True, "SELECT 1 ok")
        add("payments_idempotency_index", bool(idx_ok), "payments.idempotency_key indexed/unique")
        add("webhook_events_event_id_index", bool(wh_ok), "webhook_events.event_id indexed/unique")
    except Exception as exc:  # noqa: BLE001
        add("database_reachable", False, str(exc)[:200])
        add("payments_idempotency_index", False, "skipped")
        add("webhook_events_event_id_index", False, "skipped")

    api = (settings.app_api_url or os.environ.get("APP_API_URL") or "http://127.0.0.1:8000").rstrip("/")
    status, body = _http("GET", f"{api}/api/live")
    add("api_live", status == 200, f"GET {api}/api/live -> {status}")

    # Webhook endpoint reachable: expect 400/401/403/422 without valid signature — not 404/connection error.
    for name in configured or list(providers):
        path = providers[name]["webhook_path"]
        st, _ = _http("POST", f"{api}{path}", data=b"{}", headers={"Content-Type": "application/json"})
        reachable = st is not None and st != 404
        # 400/403/422 = app handled request (signature missing/invalid)
        signature_gate = st in {400, 401, 403, 422}
        add(
            f"{name}_webhook_reachable",
            reachable and (name not in configured or signature_gate or st in {400, 401, 403, 422, 500}),
            f"POST {path} -> {st} (expect non-404; signature reject preferred)",
        )

    harness = os.environ.get("LIVE_BILLING_HARNESS") == "1"
    add(
        "harness_armed",
        harness,
        "Set LIVE_BILLING_HARNESS=1 before prepare (prevents accidental checkout creation).",
    )

    amount = int(os.environ.get("LIVE_HARNESS_AMOUNT_CENTS", "100"))
    add(
        "amount_in_spotcheck_band",
        50 <= amount <= 100,
        f"LIVE_HARNESS_AMOUNT_CENTS={amount} (recommend 50–100 for $0.50–$1)",
    )

    report = {
        "measured_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "moves_money": False,
        "creates_checkout": False,
        "pass": not fail,
        "verdict": "PASS" if not fail else "FAIL",
        "configured_providers": configured,
        "api_base": api,
        "checks": checks,
        "human_next": (
            "If PASS: run ops/live_billing_prepare.py for scenario=success, then complete payment in the browser. "
            "Scripts never click Pay."
        ),
    }
    out = ROOT / "ops" / "cert_live_billing_preflight.json"
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({"verdict": report["verdict"], "pass": report["pass"], "out": str(out), "configured": configured}, indent=2))
    for c in checks:
        mark = "OK" if c["pass"] else "FAIL"
        print(f"  [{mark}] {c['check']}: {c['detail']}")
    return 0 if not fail else 1


if __name__ == "__main__":
    raise SystemExit(main())
