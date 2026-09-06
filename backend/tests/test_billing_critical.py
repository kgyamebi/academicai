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
    body = json.dumps({"event": "charge.failed", "data": {"reference": "r1"}}).encode()
    sig = hmac.new(secret.encode(), body, hashlib.sha512).hexdigest()
    response = client.post("/api/billing/webhooks/paystack", content=body, headers={"x-paystack-signature": sig})
    assert response.status_code == 200
    get_settings.cache_clear()
