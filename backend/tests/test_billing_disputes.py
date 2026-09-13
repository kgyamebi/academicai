"""Dispute / chargeback webhooks — Stripe, Paystack, Flutterwave sandbox shapes."""

from __future__ import annotations

import json

from app.db.session import SessionLocal
from app.models.billing import Payment, Plan, Subscription
from app.models.user import User
from app.services.billing import apply_successful_payment
from app.services.billing_disputes import open_dispute, resolve_dispute
from app.services.credits import available_credits
from app.services.subscription_fsm import assert_initial_status


def _paid_subscription(db, email: str, provider: str) -> tuple[User, Payment, Subscription]:
    user = User(email=email, password_hash="x", full_name="D", is_guest=False)
    db.add(user)
    db.flush()
    plan = db.query(Plan).filter(Plan.slug == "student").one()
    payment = Payment(
        user_id=user.id,
        provider=provider,
        amount_cents=199,
        currency="USD",
        status="pending",
        purpose="subscription",
        raw_payload={"plan": "student", "logical_purchase_id": f"disp:{email}"},
        idempotency_key=f"disp:{email}",
    )
    db.add(payment)
    db.flush()
    apply_successful_payment(db, payment, f"evt_ok_{provider}_{email}", {"type": "checkout.session.completed"})
    db.flush()
    sub = db.query(Subscription).filter(Subscription.user_id == user.id, Subscription.status == "active").one()
    payment.subscription_id = sub.id
    db.flush()
    return user, payment, sub


def test_stripe_dispute_suspends_then_won_restores(client, monkeypatch):
    db = SessionLocal()
    try:
        user, payment, sub = _paid_subscription(db, "disp-stripe@example.com", "stripe")
        db.commit()
        payment_id = str(payment.id)
        sub_id = sub.id
    finally:
        db.close()

    opened = json.dumps(
        {
            "id": "evt_dispute_open",
            "type": "charge.dispute.created",
            "data": {
                "object": {
                    "id": "dp_test_1",
                    "status": "needs_response",
                    "metadata": {"payment_id": payment_id},
                }
            },
        }
    ).encode()
    monkeypatch.setattr("app.api.v1.billing.verify_stripe_signature", lambda _p, _s: json.loads(opened.decode()))
    resp = client.post("/api/billing/webhooks/stripe", content=opened, headers={"Stripe-Signature": "t=1,v1=x"})
    assert resp.status_code == 200
    db = SessionLocal()
    try:
        sub = db.get(Subscription, sub_id)
        pay = db.get(Payment, payment.id) if False else db.get(Payment, __import__("uuid").UUID(payment_id))
        assert pay.status == "disputed"
        assert sub.status == "suspended"
    finally:
        db.close()

    closed = json.dumps(
        {
            "id": "evt_dispute_won",
            "type": "charge.dispute.closed",
            "data": {
                "object": {
                    "id": "dp_test_1",
                    "status": "won",
                    "metadata": {"payment_id": payment_id},
                }
            },
        }
    ).encode()
    monkeypatch.setattr("app.api.v1.billing.verify_stripe_signature", lambda _p, _s: json.loads(closed.decode()))
    resp = client.post("/api/billing/webhooks/stripe", content=closed, headers={"Stripe-Signature": "t=1,v1=x"})
    assert resp.status_code == 200
    db = SessionLocal()
    try:
        sub = db.get(Subscription, sub_id)
        pay = db.get(Payment, __import__("uuid").UUID(payment_id))
        assert pay.status == "successful"
        assert sub.status == "active"
        assert sub.disputed_at is None
    finally:
        db.close()


def test_paystack_dispute_lost_cancels_and_does_not_grant_extra(client, monkeypatch):
    secret = "sk_test_paystack_dispute"
    monkeypatch.setenv("PAYSTACK_SECRET_KEY", secret)
    from app.config import get_settings

    get_settings.cache_clear()
    db = SessionLocal()
    try:
        user, payment, sub = _paid_subscription(db, "disp-paystack@example.com", "paystack")
        db.commit()
        payment_id = str(payment.id)
        sub_id = sub.id
        user_id = user.id
    finally:
        db.close()

    body = json.dumps(
        {
            "event": "charge.dispute.create",
            "data": {"reference": payment_id, "metadata": {"payment_id": payment_id}, "status": "pending"},
        }
    ).encode()
    import hashlib
    import hmac

    sig = hmac.new(secret.encode(), body, hashlib.sha512).hexdigest()
    resp = client.post("/api/billing/webhooks/paystack", content=body, headers={"x-paystack-signature": sig})
    assert resp.status_code == 200

    lost = json.dumps(
        {
            "event": "charge.dispute.resolve",
            "data": {"reference": payment_id, "metadata": {"payment_id": payment_id}, "status": "lost"},
        }
    ).encode()
    sig2 = hmac.new(secret.encode(), lost, hashlib.sha512).hexdigest()
    resp = client.post("/api/billing/webhooks/paystack", content=lost, headers={"x-paystack-signature": sig2})
    assert resp.status_code == 200
    db = SessionLocal()
    try:
        sub = db.get(Subscription, sub_id)
        pay = db.get(Payment, __import__("uuid").UUID(payment_id))
        assert pay.status == "refunded"
        assert sub.status == "cancelled"
        user = db.get(User, user_id)
        assert float(available_credits(db, user)) == 0
    finally:
        db.close()
    get_settings.cache_clear()


def test_flutterwave_dispute_open_and_won(client, monkeypatch):
    monkeypatch.setenv("FLUTTERWAVE_WEBHOOK_HASH", "flw_hash_test")
    from app.config import get_settings

    get_settings.cache_clear()
    db = SessionLocal()
    try:
        user, payment, sub = _paid_subscription(db, "disp-flw@example.com", "flutterwave")
        db.commit()
        payment_id = str(payment.id)
        sub_id = sub.id
    finally:
        db.close()

    opened = json.dumps(
        {
            "event": "dispute.created",
            "data": {"id": "flw_dp_1", "tx_ref": payment_id, "meta": {"payment_id": payment_id}, "status": "pending"},
        }
    ).encode()
    resp = client.post("/api/billing/webhooks/flutterwave", content=opened, headers={"verif-hash": "flw_hash_test"})
    assert resp.status_code == 200
    db = SessionLocal()
    try:
        assert db.get(Subscription, sub_id).status == "suspended"
        assert db.get(Payment, __import__("uuid").UUID(payment_id)).status == "disputed"
    finally:
        db.close()

    won = json.dumps(
        {
            "event": "dispute.resolved",
            "data": {"id": "flw_dp_1_res", "tx_ref": payment_id, "meta": {"payment_id": payment_id}, "status": "won"},
        }
    ).encode()
    resp = client.post("/api/billing/webhooks/flutterwave", content=won, headers={"verif-hash": "flw_hash_test"})
    assert resp.status_code == 200
    db = SessionLocal()
    try:
        assert db.get(Subscription, sub_id).status == "active"
        assert db.get(Payment, __import__("uuid").UUID(payment_id)).status == "successful"
    finally:
        db.close()
    get_settings.cache_clear()


def test_open_dispute_does_not_clawback_credits_until_lost(client):
    db = SessionLocal()
    try:
        user = User(email="disp-credits@example.com", password_hash="x", full_name="C", is_guest=False)
        db.add(user)
        db.flush()
        payment = Payment(
            user_id=user.id,
            provider="stripe",
            amount_cents=299,
            currency="USD",
            status="pending",
            purpose="credits",
            raw_payload={"credits": 10, "pack": "credits_10", "logical_purchase_id": "credits-disp"},
        )
        db.add(payment)
        db.flush()
        apply_successful_payment(db, payment, "evt_cred_ok", {"ok": True})
        db.commit()
        before = float(available_credits(db, user))
        open_dispute(db, payment, "evt_dp_open", {"type": "charge.dispute.created"})
        db.commit()
        assert float(available_credits(db, user)) == before
        resolve_dispute(db, payment, "evt_dp_lost", {"type": "charge.dispute.closed"}, won=False)
        db.commit()
        assert float(available_credits(db, user)) == 0
    finally:
        db.close()
