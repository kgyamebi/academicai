"""Sandbox-faithful billing verification — all 8 scenarios × Stripe/Paystack/Flutterwave.

No live keys are used. Payloads match documented sandbox webhook shapes.
When sandbox API keys are absent (this environment), logic is verified via
signed/mocked webhook HTTP and service-layer races against the same guards
production would use (unique event_id, provider_event_id, payment row lock).
"""

from __future__ import annotations

import hashlib
import hmac
import json
import threading
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from uuid import uuid4

import pytest

from app.core.time import utcnow
from app.db.session import SessionLocal
from app.models.billing import Payment, PaymentTransaction
from app.models.user import User
from app.services.billing import (
    _pending_payment,
    apply_refund,
    apply_successful_payment,
    mark_payment_failed,
    record_webhook_event,
)
from app.services.billing_reconcile import reconcile_against_provider_snapshot
from app.services.credits import available_credits

PROCESSORS = ("stripe", "paystack", "flutterwave")


def _register(client, email: str) -> str:
    response = client.post(
        "/api/auth/register",
        json={"email": email, "password": "password12", "full_name": "Sandbox"},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def _pending_credit_payment(db, user, provider: str, *, cents: int = 299, credits: int = 10) -> Payment:
    payment = Payment(
        user_id=user.id,
        provider=provider,
        amount_cents=cents,
        currency="USD",
        status="pending",
        purpose="credits",
        raw_payload={"credits": credits, "pack": "credits_10"},
        idempotency_key=f"sandbox:{provider}:{user.id}:{uuid4().hex}",
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)
    return payment


# --- Scenario 1: Idempotent charge retry ---


@pytest.mark.parametrize("provider", PROCESSORS)
def test_s1_idempotent_charge_retry_same_key(client, provider):
    _register(client, f"s1-{provider}@example.com")
    db = SessionLocal()
    user = db.query(User).filter(User.email == f"s1-{provider}@example.com").one()
    key = f"idem-{provider}-{uuid4().hex}"
    first = _pending_payment(db, user, provider, 199, "USD", "subscription", key, {"plan": "student"})
    db.commit()
    second = _pending_payment(db, user, provider, 199, "USD", "subscription", key, {"plan": "student"})
    assert first.id == second.id
    assert db.query(Payment).filter(Payment.idempotency_key == key).count() == 1
    db.close()


# --- Scenario 2: Duplicate webhook delivery ---


@pytest.mark.parametrize("provider", PROCESSORS)
def test_s2_duplicate_webhook_no_double_credit(client, provider):
    _register(client, f"s2-{provider}@example.com")
    db = SessionLocal()
    user = db.query(User).filter(User.email == f"s2-{provider}@example.com").one()
    payment = _pending_credit_payment(db, user, provider)
    event_id = f"evt_dup_{provider}_{uuid4().hex}"
    apply_successful_payment(db, payment, event_id, {"type": "checkout.session.completed", "provider": provider})
    db.commit()
    credits_after = float(available_credits(db, user))
    apply_successful_payment(db, db.get(Payment, payment.id), event_id, {"type": "checkout.session.completed"})
    db.commit()
    assert float(available_credits(db, user)) == credits_after
    assert (
        db.query(PaymentTransaction)
        .filter(PaymentTransaction.provider_event_id == event_id)
        .count()
        == 1
    )
    payload = b"{}"
    assert record_webhook_event(db, provider, event_id, "success", payload, mark_processed=True) is True
    db.commit()
    assert record_webhook_event(db, provider, event_id, "success", payload, mark_processed=True) is False
    db.close()


def test_s2_stripe_http_duplicate_webhook(client, monkeypatch):
    token = _register(client, "s2-stripe-http@example.com")
    db = SessionLocal()
    user = db.query(User).filter(User.email == "s2-stripe-http@example.com").one()
    payment = _pending_credit_payment(db, user, "stripe")
    payment_id = str(payment.id)
    db.close()
    event_id = f"evt_http_dup_{uuid4().hex}"
    body = json.dumps(
        {
            "id": event_id,
            "type": "checkout.session.completed",
            "data": {"object": {"metadata": {"payment_id": payment_id}}},
        }
    ).encode()
    monkeypatch.setattr(
        "app.api.v1.billing.verify_stripe_signature",
        lambda _p, _s: json.loads(body.decode()),
    )
    first = client.post("/api/billing/webhooks/stripe", content=body, headers={"Stripe-Signature": "t=1,v1=x"})
    second = client.post("/api/billing/webhooks/stripe", content=body, headers={"Stripe-Signature": "t=1,v1=x"})
    assert first.status_code == 200
    assert second.status_code == 200
    assert second.json().get("duplicate") is True
    db = SessionLocal()
    user = db.query(User).filter(User.email == "s2-stripe-http@example.com").one()
    assert float(available_credits(db, user)) == 10
    assert db.query(PaymentTransaction).filter(PaymentTransaction.provider_event_id == event_id).count() == 1
    db.close()
    _ = token


def test_s2_paystack_http_duplicate(client, monkeypatch):
    secret = "sk_test_paystack_sandbox"
    monkeypatch.setenv("PAYSTACK_SECRET_KEY", secret)
    from app.config import get_settings

    get_settings.cache_clear()
    _register(client, "s2-paystack-http@example.com")
    db = SessionLocal()
    user = db.query(User).filter(User.email == "s2-paystack-http@example.com").one()
    payment = _pending_credit_payment(db, user, "paystack")
    payment_id = str(payment.id)
    db.close()
    body = json.dumps(
        {
            "event": "charge.success",
            "data": {"reference": "ref_dup", "metadata": {"payment_id": payment_id}},
        }
    ).encode()
    sig = hmac.new(secret.encode(), body, hashlib.sha512).hexdigest()
    headers = {"x-paystack-signature": sig}
    assert client.post("/api/billing/webhooks/paystack", content=body, headers=headers).status_code == 200
    second = client.post("/api/billing/webhooks/paystack", content=body, headers=headers)
    assert second.status_code == 200
    assert second.json().get("duplicate") is True
    db = SessionLocal()
    user = db.query(User).filter(User.email == "s2-paystack-http@example.com").one()
    assert float(available_credits(db, user)) == 10
    db.close()
    get_settings.cache_clear()


def test_s2_flutterwave_http_duplicate(client, monkeypatch):
    secret = "flw_test_hash"
    monkeypatch.setenv("FLUTTERWAVE_WEBHOOK_HASH", secret)
    from app.config import get_settings

    get_settings.cache_clear()
    _register(client, "s2-flw-http@example.com")
    db = SessionLocal()
    user = db.query(User).filter(User.email == "s2-flw-http@example.com").one()
    payment = _pending_credit_payment(db, user, "flutterwave")
    payment_id = str(payment.id)
    db.close()
    body = json.dumps(
        {
            "event": "charge.completed",
            "data": {"id": "flw_dup", "tx_ref": payment_id, "status": "successful", "meta": {"payment_id": payment_id}},
        }
    ).encode()
    headers = {"verif-hash": secret}
    assert client.post("/api/billing/webhooks/flutterwave", content=body, headers=headers).status_code == 200
    second = client.post("/api/billing/webhooks/flutterwave", content=body, headers=headers)
    assert second.status_code == 200
    assert second.json().get("duplicate") is True
    db = SessionLocal()
    user = db.query(User).filter(User.email == "s2-flw-http@example.com").one()
    assert float(available_credits(db, user)) == 10
    db.close()
    get_settings.cache_clear()


# --- Scenario 3: Out-of-order webhook delivery ---


@pytest.mark.parametrize("provider", PROCESSORS)
def test_s3_refund_before_success_defers_then_applies(client, provider):
    _register(client, f"s3-{provider}@example.com")
    db = SessionLocal()
    user = db.query(User).filter(User.email == f"s3-{provider}@example.com").one()
    payment = _pending_credit_payment(db, user, provider)
    early = apply_refund(db, payment, f"evt_early_refund_{provider}", {"refund": True}, amount_cents=299)
    assert early is False
    assert payment.status == "pending"
    assert float(available_credits(db, user)) == 0
    apply_successful_payment(db, payment, f"evt_late_ok_{provider}", {"type": "checkout.session.completed"})
    db.commit()
    assert float(available_credits(db, user)) == 10
    applied = apply_refund(db, db.get(Payment, payment.id), f"evt_early_refund_{provider}", {"refund": True}, amount_cents=299)
    assert applied is True
    db.commit()
    assert db.get(Payment, payment.id).status == "refunded"
    assert float(available_credits(db, user)) == 0
    db.close()


@pytest.mark.parametrize("provider", PROCESSORS)
def test_s3_failed_then_success_grants(client, provider):
    _register(client, f"s3f-{provider}@example.com")
    db = SessionLocal()
    user = db.query(User).filter(User.email == f"s3f-{provider}@example.com").one()
    payment = _pending_credit_payment(db, user, provider)
    mark_payment_failed(db, payment, f"evt_fail_{provider}", {"type": "payment_failed"})
    db.commit()
    apply_successful_payment(db, db.get(Payment, payment.id), f"evt_ok_{provider}", {"type": "succeeded"})
    db.commit()
    assert db.get(Payment, payment.id).status == "successful"
    assert float(available_credits(db, user)) == 10
    db.close()


def test_s3_stripe_http_refund_before_success_returns_503(client, monkeypatch):
    _register(client, "s3-stripe-oo@example.com")
    db = SessionLocal()
    user = db.query(User).filter(User.email == "s3-stripe-oo@example.com").one()
    payment = _pending_credit_payment(db, user, "stripe")
    payment_id = str(payment.id)
    db.close()
    refund_body = json.dumps(
        {
            "id": f"evt_refund_first_{uuid4().hex}",
            "type": "charge.refunded",
            "data": {"object": {"metadata": {"payment_id": payment_id}, "amount_refunded": 299}},
        }
    ).encode()
    monkeypatch.setattr(
        "app.api.v1.billing.verify_stripe_signature",
        lambda _p, _s: json.loads(refund_body.decode()),
    )
    response = client.post(
        "/api/billing/webhooks/stripe",
        content=refund_body,
        headers={"Stripe-Signature": "t=1,v1=x"},
    )
    assert response.status_code == 503


# --- Scenario 4: Concurrent webhook delivery ---


@pytest.mark.parametrize("provider", PROCESSORS)
def test_s4_concurrent_same_event_id_single_credit(client, provider):
    _register(client, f"s4-{provider}@example.com")
    db = SessionLocal()
    user = db.query(User).filter(User.email == f"s4-{provider}@example.com").one()
    payment = _pending_credit_payment(db, user, provider)
    payment_id = payment.id
    user_id = user.id
    db.close()
    event_id = f"evt_race_{provider}_{uuid4().hex}"
    barrier = threading.Barrier(2)
    errors: list[str] = []

    def worker() -> None:
        local = SessionLocal()
        try:
            barrier.wait(timeout=5)
            pay = local.get(Payment, payment_id)
            apply_successful_payment(local, pay, event_id, {"type": "checkout.session.completed"})
            local.commit()
        except Exception as exc:  # noqa: BLE001
            errors.append(str(exc))
            local.rollback()
        finally:
            local.close()

    with ThreadPoolExecutor(max_workers=2) as pool:
        list(pool.map(lambda _: worker(), range(2)))

    db = SessionLocal()
    user = db.get(User, user_id)
    txns = (
        db.query(PaymentTransaction)
        .filter(PaymentTransaction.provider_event_id == event_id)
        .count()
    )
    assert txns == 1
    assert float(available_credits(db, user)) == 10
    db.close()


def test_s4_concurrent_webhook_event_unique_constraint(client):
    event_id = f"evt_wh_race_{uuid4().hex}"
    barrier = threading.Barrier(2)
    results: list[bool] = []

    def worker() -> None:
        local = SessionLocal()
        try:
            barrier.wait(timeout=5)
            ok = record_webhook_event(local, "stripe", event_id, "checkout.session.completed", b"{}", mark_processed=True)
            local.commit()
            results.append(ok)
        except Exception:
            local.rollback()
            results.append(False)
        finally:
            local.close()

    with ThreadPoolExecutor(max_workers=2) as pool:
        list(pool.map(lambda _: worker(), range(2)))
    assert results.count(True) == 1
    assert results.count(False) == 1


# --- Scenario 5: Declined / failed charge ---


@pytest.mark.parametrize("provider", PROCESSORS)
def test_s5_failed_charge_no_credits(client, provider):
    _register(client, f"s5-{provider}@example.com")
    db = SessionLocal()
    user = db.query(User).filter(User.email == f"s5-{provider}@example.com").one()
    payment = _pending_credit_payment(db, user, provider)
    mark_payment_failed(db, payment, f"evt_declined_{provider}", {"decline_code": "insufficient_funds"})
    db.commit()
    assert db.get(Payment, payment.id).status == "failed"
    assert float(available_credits(db, user)) == 0
    assert (
        db.query(PaymentTransaction)
        .filter(PaymentTransaction.payment_id == payment.id, PaymentTransaction.status == "failed")
        .count()
        == 1
    )
    db.close()


def test_s5_paystack_failed_webhook_http(client, monkeypatch):
    secret = "sk_test_decline"
    monkeypatch.setenv("PAYSTACK_SECRET_KEY", secret)
    from app.config import get_settings

    get_settings.cache_clear()
    _register(client, "s5-paystack@example.com")
    db = SessionLocal()
    user = db.query(User).filter(User.email == "s5-paystack@example.com").one()
    payment = _pending_credit_payment(db, user, "paystack")
    payment_id = str(payment.id)
    db.close()
    body = json.dumps(
        {"event": "charge.failed", "data": {"reference": "declined1", "metadata": {"payment_id": payment_id}}}
    ).encode()
    sig = hmac.new(secret.encode(), body, hashlib.sha512).hexdigest()
    assert client.post("/api/billing/webhooks/paystack", content=body, headers={"x-paystack-signature": sig}).status_code == 200
    db = SessionLocal()
    from uuid import UUID

    row = db.get(Payment, UUID(payment_id))
    assert row is not None
    assert row.status == "failed"
    user = db.query(User).filter(User.email == "s5-paystack@example.com").one()
    assert float(available_credits(db, user)) == 0
    db.close()
    get_settings.cache_clear()


# --- Scenario 6: Partial and full refunds ---


@pytest.mark.parametrize("provider", PROCESSORS)
def test_s6_full_and_double_refund(client, provider):
    _register(client, f"s6-{provider}@example.com")
    db = SessionLocal()
    user = db.query(User).filter(User.email == f"s6-{provider}@example.com").one()
    payment = _pending_credit_payment(db, user, provider)
    apply_successful_payment(db, payment, f"evt_ok_{provider}", {})
    db.commit()
    assert apply_refund(db, db.get(Payment, payment.id), f"evt_ref_{provider}", {}, amount_cents=299) is True
    db.commit()
    assert float(available_credits(db, user)) == 0
    assert db.get(Payment, payment.id).status == "refunded"
    # Same event id
    assert apply_refund(db, db.get(Payment, payment.id), f"evt_ref_{provider}", {}, amount_cents=299) is True
    # Different event id after full refund — no-op, no second clawback
    assert apply_refund(db, db.get(Payment, payment.id), f"evt_ref2_{provider}", {}, amount_cents=299) is True
    db.commit()
    assert float(available_credits(db, user)) == 0
    db.close()


@pytest.mark.parametrize("provider", PROCESSORS)
def test_s6_partial_then_remainder_no_over_clawback(client, provider):
    _register(client, f"s6p-{provider}@example.com")
    db = SessionLocal()
    user = db.query(User).filter(User.email == f"s6p-{provider}@example.com").one()
    payment = _pending_credit_payment(db, user, provider, cents=1000, credits=10)
    apply_successful_payment(db, payment, f"evt_okp_{provider}", {})
    db.commit()
    assert apply_refund(db, db.get(Payment, payment.id), f"evt_p1_{provider}", {}, amount_cents=400) is True
    db.commit()
    assert float(available_credits(db, user)) == 6
    assert db.get(Payment, payment.id).status == "partially_refunded"
    assert apply_refund(db, db.get(Payment, payment.id), f"evt_p2_{provider}", {}, amount_cents=600) is True
    db.commit()
    assert float(available_credits(db, user)) == 0
    assert db.get(Payment, payment.id).status == "refunded"
    assert apply_refund(db, db.get(Payment, payment.id), f"evt_p3_{provider}", {}, amount_cents=100) is True
    db.commit()
    assert float(available_credits(db, user)) == 0
    db.close()


# --- Scenario 7: Webhook signature verification ---


def test_s7_stripe_forged_rejected(client, monkeypatch):
    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", "whsec_test")
    from app.config import get_settings

    get_settings.cache_clear()
    body = b'{"id":"evt_forged","type":"checkout.session.completed"}'
    ts = str(int(utcnow().timestamp()))
    response = client.post(
        "/api/billing/webhooks/stripe",
        content=body,
        headers={"Stripe-Signature": f"t={ts},v1=forged"},
    )
    assert response.status_code == 400
    get_settings.cache_clear()


def test_s7_paystack_unsigned_rejected(client, monkeypatch):
    monkeypatch.setenv("PAYSTACK_SECRET_KEY", "sk_test")
    from app.config import get_settings

    get_settings.cache_clear()
    response = client.post("/api/billing/webhooks/paystack", content=b'{"event":"charge.success"}')
    assert response.status_code == 400
    get_settings.cache_clear()


def test_s7_flutterwave_bad_hash_rejected(client, monkeypatch):
    monkeypatch.setenv("FLUTTERWAVE_WEBHOOK_HASH", "expected")
    from app.config import get_settings

    get_settings.cache_clear()
    response = client.post(
        "/api/billing/webhooks/flutterwave",
        content=b'{"data":{"status":"successful"}}',
        headers={"verif-hash": "wrong"},
    )
    assert response.status_code == 400
    get_settings.cache_clear()


# --- Scenario 8: Reconciliation ---


def test_s8_reconcile_flags_intentional_mismatch(client):
    _register(client, "s8-recon@example.com")
    db = SessionLocal()
    user = db.query(User).filter(User.email == "s8-recon@example.com").one()
    payment = _pending_credit_payment(db, user, "stripe")
    apply_successful_payment(db, payment, "evt_recon_ok", {})
    db.commit()
    payment = db.get(Payment, payment.id)
    payment.amount_cents = 1  # intentional corruption
    db.commit()
    snapshot = [
        {
            "provider": "stripe",
            "provider_payment_id": payment.provider_payment_id or "evt_recon_ok",
            "amount_cents": 299,
            "currency": "USD",
            "status": "successful",
        }
    ]
    # provider_payment_id was set to event id in apply_successful_payment
    payment = db.get(Payment, payment.id)
    snapshot[0]["provider_payment_id"] = payment.provider_payment_id
    report = reconcile_against_provider_snapshot(db, snapshot)
    assert report["ok"] is False
    kinds = {m["kind"] for m in report["mismatches"]}
    assert "amount_mismatch" in kinds
    db.close()


def test_s8_reconcile_clean_match(client):
    _register(client, "s8-clean@example.com")
    db = SessionLocal()
    user = db.query(User).filter(User.email == "s8-clean@example.com").one()
    payment = _pending_credit_payment(db, user, "paystack")
    apply_successful_payment(db, payment, "evt_clean", {})
    db.commit()
    payment = db.get(Payment, payment.id)
    snapshot = [
        {
            "provider": "paystack",
            "provider_payment_id": payment.provider_payment_id,
            "amount_cents": payment.amount_cents,
            "currency": payment.currency,
            "status": "successful",
        }
    ]
    report = reconcile_against_provider_snapshot(db, snapshot)
    assert report["ok"] is True
    assert report["mismatch_count"] == 0
    db.close()


def test_sandbox_keys_absent_documented():
    from pathlib import Path
    import json as _json

    keys = _json.loads((Path(__file__).resolve().parents[2] / "ops" / "cert_payment_keys.json").read_text())
    assert keys["any_provider_key"] is False
    assert keys["live_charges_executed"] is False
