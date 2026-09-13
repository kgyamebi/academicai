import hashlib
import hmac
import json
from decimal import Decimal
from uuid import uuid4

from app.db.session import SessionLocal
from app.models.billing import Payment
from app.models.user import User
from app.services.billing import apply_successful_payment, record_webhook_event
from app.services.credits import consume_reservation, refund_reservation, reserve_credits


def _register(client, email: str):
    response = client.post(
        "/api/auth/register",
        json={"email": email, "password": "password12", "full_name": "Payer"},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def test_checkout_without_provider_keys_fails_closed(client):
    token = _register(client, "bill-nokey@example.com")
    response = client.post(
        "/api/billing/checkout",
        json={"plan_slug": "student", "provider": "stripe", "currency": "USD"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 503
    assert "not configured" in response.json()["error"].lower() or response.status_code == 503


def test_guest_cannot_checkout(client):
    guest = client.post("/api/auth/guest")
    response = client.post(
        "/api/billing/checkout",
        json={"plan_slug": "student", "provider": "stripe", "currency": "USD"},
        headers={"Authorization": f"Bearer {guest.json()['access_token']}"},
    )
    assert response.status_code == 401


def test_webhook_replay_is_idempotent(client):
    token = _register(client, "bill-replay@example.com")
    db = SessionLocal()
    user = db.query(User).filter(User.email == "bill-replay@example.com").one()
    payment = Payment(
        user_id=user.id,
        provider="stripe",
        amount_cents=199,
        currency="USD",
        status="pending",
        purpose="subscription",
        raw_payload={"plan": "student"},
    )
    db.add(payment)
    db.commit()
    event_id = f"evt_{uuid4().hex}"
    payload = json.dumps({"id": event_id, "type": "checkout.session.completed"}).encode()
    assert record_webhook_event(db, "stripe", event_id, "checkout.session.completed", payload) is True
    apply_successful_payment(db, payment, event_id, {"id": event_id})
    db.commit()
    payment_id = payment.id
    first_status = db.get(Payment, payment_id).status
    assert record_webhook_event(db, "stripe", event_id, "checkout.session.completed", payload) is False
    apply_successful_payment(db, db.get(Payment, payment_id), event_id, {"id": event_id})
    db.commit()
    again = db.get(Payment, payment_id)
    assert first_status == "successful"
    assert again.status == "successful"
    db.close()
    billing = client.get("/api/billing", headers={"Authorization": f"Bearer {token}"})
    assert billing.status_code == 200
    assert billing.json()["plan"]["slug"] == "student"


def test_credit_ledger_reserve_consume_refund(client):
    _register(client, "bill-credits@example.com")
    db = SessionLocal()
    user = db.query(User).filter(User.email == "bill-credits@example.com").one()
    from app.services.credits import grant_credits

    grant_credits(db, user, Decimal("10"))
    job_id = uuid4()
    reserve_credits(db, user, "full", job_id)
    db.commit()
    remaining_after_reserve = float(db.query(User).filter(User.id == user.id).one().credits[0].remaining)
    assert remaining_after_reserve == 8
    consume_reservation(db, job_id)
    db.commit()
    wallet = db.query(User).filter(User.id == user.id).one().credits[0]
    assert float(wallet.remaining) == 8
    assert float(wallet.reserved) == 0
    job_b = uuid4()
    reserve_credits(db, user, "full", job_b)
    refund_reservation(db, job_b)
    db.commit()
    wallet = db.query(User).filter(User.id == user.id).one().credits[0]
    assert float(wallet.remaining) == 8
    db.close()


def test_paystack_rejects_bad_signature(client, monkeypatch):
    monkeypatch.setenv("PAYSTACK_SECRET_KEY", "secret")
    from app.config import get_settings

    get_settings.cache_clear()
    body = b'{"event":"charge.success","data":{}}'
    response = client.post("/api/billing/webhooks/paystack", content=body, headers={"x-paystack-signature": "nope"})
    assert response.status_code == 400
    get_settings.cache_clear()


def test_flutterwave_rejects_bad_hash(client, monkeypatch):
    monkeypatch.setenv("FLUTTERWAVE_WEBHOOK_HASH", "expected-hash")
    from app.config import get_settings

    get_settings.cache_clear()
    response = client.post(
        "/api/billing/webhooks/flutterwave",
        content=b'{"data":{"status":"successful"}}',
        headers={"verif-hash": "wrong"},
    )
    assert response.status_code == 400
    get_settings.cache_clear()


def test_paystack_valid_signature_roundtrip(client, monkeypatch):
    secret = "paystack_live_test"
    monkeypatch.setenv("PAYSTACK_SECRET_KEY", secret)
    from app.config import get_settings

    get_settings.cache_clear()
    token = _register(client, "bill-paystack-sig@example.com")
    db = SessionLocal()
    user = db.query(User).filter(User.email == "bill-paystack-sig@example.com").one()
    payment = Payment(
        user_id=user.id,
        provider="paystack",
        amount_cents=199,
        currency="USD",
        status="pending",
        purpose="subscription",
        raw_payload={},
    )
    db.add(payment)
    db.commit()
    payment_id = str(payment.id)
    db.close()
    body = json.dumps(
        {"event": "charge.failed", "data": {"reference": "r1", "metadata": {"payment_id": payment_id}}}
    ).encode()
    sig = hmac.new(secret.encode(), body, hashlib.sha512).hexdigest()
    response = client.post("/api/billing/webhooks/paystack", content=body, headers={"x-paystack-signature": sig})
    assert response.status_code == 200
    get_settings.cache_clear()
    _ = token


def test_failed_then_successful_webhook_still_grants(client):
    token = _register(client, "bill-order@example.com")
    db = SessionLocal()
    user = db.query(User).filter(User.email == "bill-order@example.com").one()
    payment = Payment(
        user_id=user.id,
        provider="stripe",
        amount_cents=199,
        currency="USD",
        status="pending",
        purpose="subscription",
        raw_payload={"plan": "student"},
    )
    db.add(payment)
    db.commit()
    from app.services.billing import mark_payment_failed

    mark_payment_failed(db, payment, "evt_fail_first", {"type": "payment_intent.payment_failed"})
    db.commit()
    assert db.get(Payment, payment.id).status == "failed"
    apply_successful_payment(db, db.get(Payment, payment.id), "evt_success_later", {"type": "checkout.session.completed"})
    db.commit()
    assert db.get(Payment, payment.id).status == "successful"
    db.close()
    billing = client.get("/api/billing", headers={"Authorization": f"Bearer {token}"})
    assert billing.json()["plan"]["slug"] == "student"


def test_success_then_late_failure_does_not_revoke(client):
    _register(client, "bill-latefail@example.com")
    db = SessionLocal()
    user = db.query(User).filter(User.email == "bill-latefail@example.com").one()
    payment = Payment(
        user_id=user.id,
        provider="stripe",
        amount_cents=199,
        currency="USD",
        status="pending",
        purpose="subscription",
        raw_payload={"plan": "student"},
    )
    db.add(payment)
    db.commit()
    apply_successful_payment(db, payment, "evt_ok", {"ok": True})
    db.commit()
    from app.services.billing import mark_payment_failed

    mark_payment_failed(db, db.get(Payment, payment.id), "evt_late_fail", {"failed": True})
    db.commit()
    assert db.get(Payment, payment.id).status == "successful"
    db.close()


def test_refund_claws_back_credits_once(client):
    _register(client, "bill-refund@example.com")
    db = SessionLocal()
    user = db.query(User).filter(User.email == "bill-refund@example.com").one()
    payment = Payment(
        user_id=user.id,
        provider="stripe",
        amount_cents=299,
        currency="USD",
        status="pending",
        purpose="credits",
        raw_payload={"credits": 10, "pack": "credits_10"},
    )
    db.add(payment)
    db.commit()
    apply_successful_payment(db, payment, "evt_credit_ok", {"ok": True})
    db.commit()
    from app.services.billing import apply_refund
    from app.services.credits import available_credits

    user = db.query(User).filter(User.email == "bill-refund@example.com").one()
    assert float(available_credits(db, user)) == 10
    apply_refund(db, db.get(Payment, payment.id), "evt_refund", {"refund": True})
    db.commit()
    apply_refund(db, db.get(Payment, payment.id), "evt_refund", {"refund": True})
    db.commit()
    user = db.query(User).filter(User.email == "bill-refund@example.com").one()
    assert db.get(Payment, payment.id).status == "refunded"
    assert float(available_credits(db, user)) == 0
    db.close()


def test_partial_refund_claws_proportional_credits(client):
    _register(client, "bill-partial@example.com")
    db = SessionLocal()
    user = db.query(User).filter(User.email == "bill-partial@example.com").one()
    payment = Payment(
        user_id=user.id,
        provider="paystack",
        amount_cents=1000,
        currency="USD",
        status="pending",
        purpose="credits",
        raw_payload={"credits": 10, "pack": "credits_10"},
    )
    db.add(payment)
    db.commit()
    apply_successful_payment(db, payment, "evt_partial_ok", {"ok": True})
    db.commit()
    from app.services.billing import apply_refund
    from app.services.credits import available_credits

    apply_refund(db, db.get(Payment, payment.id), "evt_partial", {"partial": True}, amount_cents=500)
    db.commit()
    user = db.query(User).filter(User.email == "bill-partial@example.com").one()
    assert db.get(Payment, payment.id).status == "partially_refunded"
    assert float(available_credits(db, user)) == 5
    db.close()


def test_cancelled_charge_does_not_grant(client):
    _register(client, "bill-cancel@example.com")
    db = SessionLocal()
    user = db.query(User).filter(User.email == "bill-cancel@example.com").one()
    payment = Payment(
        user_id=user.id,
        provider="flutterwave",
        amount_cents=199,
        currency="USD",
        status="pending",
        purpose="subscription",
        raw_payload={"plan": "student"},
    )
    db.add(payment)
    db.commit()
    from app.services.billing import mark_payment_cancelled

    mark_payment_cancelled(db, payment, "evt_cancel", {"cancelled": True})
    db.commit()
    assert db.get(Payment, payment.id).status == "cancelled"
    db.close()


def test_second_subscription_cancels_the_first(client):
    token = _register(client, "bill-upgrade@example.com")
    db = SessionLocal()
    user = db.query(User).filter(User.email == "bill-upgrade@example.com").one()
    first = Payment(
        user_id=user.id,
        provider="stripe",
        amount_cents=199,
        currency="USD",
        status="pending",
        purpose="subscription",
        raw_payload={"plan": "student"},
    )
    second = Payment(
        user_id=user.id,
        provider="stripe",
        amount_cents=499,
        currency="USD",
        status="pending",
        purpose="subscription",
        raw_payload={"plan": "pro"},
    )
    db.add_all([first, second])
    db.commit()
    apply_successful_payment(db, first, "evt_sub_1", {})
    apply_successful_payment(db, second, "evt_sub_2", {})
    db.commit()
    from app.models.billing import Subscription

    active = [s for s in db.query(Subscription).filter(Subscription.user_id == user.id) if s.status == "active"]
    assert len(active) == 1
    db.close()
    billing = client.get("/api/billing", headers={"Authorization": f"Bearer {token}"})
    assert billing.status_code == 200
    assert billing.json()["plan"]["slug"] in {"pro", "researcher", "student"}


def test_expired_credits_are_unusable(client):
    from datetime import timedelta

    from app.core.time import utcnow
    from app.services.credits import available_credits, grant_credits

    _register(client, "bill-expire@example.com")
    db = SessionLocal()
    user = db.query(User).filter(User.email == "bill-expire@example.com").one()
    grant_credits(db, user, Decimal("8"))
    wallet = user.credits[0]
    wallet.expires_at = utcnow() - timedelta(days=1)
    db.commit()
    user = db.query(User).filter(User.email == "bill-expire@example.com").one()
    assert float(available_credits(db, user)) == 0
    from app.models.billing import CreditTransaction
    from app.services.credits import wallet_matches_ledger

    expired_rows = (
        db.query(CreditTransaction)
        .filter(CreditTransaction.user_id == user.id, CreditTransaction.status == "expired")
        .all()
    )
    assert len(expired_rows) == 1
    assert float(expired_rows[0].amount) == 8
    assert wallet_matches_ledger(db, user) is True
    db.close()


def test_invoice_paid_extends_period_near_expiry(client):
    from datetime import timedelta

    from app.core.time import as_utc, utcnow
    from app.models.billing import Plan, Subscription
    from app.services.billing import apply_successful_payment

    _register(client, "bill-renew@example.com")
    db = SessionLocal()
    user = db.query(User).filter(User.email == "bill-renew@example.com").one()
    plan = db.query(Plan).filter(Plan.slug == "student").one()
    sub = Subscription(
        user_id=user.id,
        plan_id=plan.id,
        status="active",
        provider="stripe",
        cancel_at_period_end=False,
        current_period_start=utcnow() - timedelta(days=28),
        current_period_end=utcnow() + timedelta(days=1),
        checks_used=3,
    )
    payment = Payment(
        user_id=user.id,
        provider="stripe",
        amount_cents=199,
        currency="USD",
        status="successful",
        purpose="subscription",
        raw_payload={"plan": "student"},
    )
    db.add_all([sub, payment])
    db.commit()
    apply_successful_payment(db, payment, "evt_invoice_paid_1", {"type": "invoice.paid"})
    db.commit()
    refreshed = db.get(Subscription, sub.id)
    assert refreshed is not None
    assert refreshed.checks_used == 0
    end = as_utc(refreshed.current_period_end)
    assert end is not None
    assert end > utcnow() + timedelta(days=20)
    db.close()


def test_checkout_rate_limit_bucket_exists():
    from app.core.rate_limit import LIMITS

    assert "checkout" in LIMITS["free"]
    assert LIMITS["free"]["checkout"] > 0


def test_failed_payment_records_analytics(client):
    from app.models.admin import AnalyticsEvent
    from app.services.billing import mark_payment_failed

    _register(client, "bill-analytics@example.com")
    db = SessionLocal()
    user = db.query(User).filter(User.email == "bill-analytics@example.com").one()
    payment = Payment(
        user_id=user.id,
        provider="stripe",
        amount_cents=199,
        currency="USD",
        status="pending",
        purpose="subscription",
        raw_payload={"plan": "student"},
    )
    db.add(payment)
    db.commit()
    mark_payment_failed(db, payment, "evt_fail_analytics", {"type": "payment_intent.payment_failed"})
    db.commit()
    events = db.query(AnalyticsEvent).filter(AnalyticsEvent.event_name == "payment_failed").all()
    assert any(e.user_id == user.id for e in events)
    db.close()
