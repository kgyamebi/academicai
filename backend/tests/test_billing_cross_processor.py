"""Cross-processor logical purchase de-duplication."""

from __future__ import annotations

from app.db.session import SessionLocal
from app.models.billing import Payment, PaymentTransaction, Subscription
from app.models.user import User
from app.services.billing import apply_successful_payment
from app.services.credits import available_credits


def test_same_logical_purchase_second_processor_does_not_double_credit(client):
    db = SessionLocal()
    try:
        user = User(email="xproc-credits@example.com", password_hash="x", full_name="X", is_guest=False)
        db.add(user)
        db.flush()
        logical = f"logical:{user.id}:credits_10"
        stripe = Payment(
            user_id=user.id,
            provider="stripe",
            amount_cents=299,
            currency="USD",
            status="pending",
            purpose="credits",
            idempotency_key=f"stripe:{logical}",
            raw_payload={"credits": 10, "pack": "credits_10", "logical_purchase_id": logical},
        )
        paystack = Payment(
            user_id=user.id,
            provider="paystack",
            amount_cents=299,
            currency="USD",
            status="pending",
            purpose="credits",
            idempotency_key=f"paystack:{logical}",
            raw_payload={"credits": 10, "pack": "credits_10", "logical_purchase_id": logical},
        )
        db.add_all([stripe, paystack])
        db.flush()
        apply_successful_payment(db, stripe, "evt_stripe_ok", {"type": "checkout.session.completed"})
        db.commit()
        credits = float(available_credits(db, user))
        apply_successful_payment(db, paystack, "evt_paystack_ok", {"event": "charge.success"})
        db.commit()
        assert float(available_credits(db, user)) == credits == 10
        assert db.get(Payment, paystack.id).status == "successful"
        types = [
            t.event_type
            for t in db.query(PaymentTransaction).filter(PaymentTransaction.payment_id == paystack.id)
        ]
        assert "payment.successful" in types
    finally:
        db.close()


def test_same_logical_purchase_does_not_create_second_subscription(client):
    db = SessionLocal()
    try:
        user = User(email="xproc-sub@example.com", password_hash="x", full_name="X", is_guest=False)
        db.add(user)
        db.flush()
        logical = f"logical:{user.id}:student:202609"
        first = Payment(
            user_id=user.id,
            provider="stripe",
            amount_cents=199,
            currency="USD",
            status="pending",
            purpose="subscription",
            idempotency_key=f"stripe:{logical}",
            raw_payload={"plan": "student", "logical_purchase_id": logical},
        )
        second = Payment(
            user_id=user.id,
            provider="flutterwave",
            amount_cents=199,
            currency="USD",
            status="pending",
            purpose="subscription",
            idempotency_key=f"flw:{logical}",
            raw_payload={"plan": "student", "logical_purchase_id": logical},
        )
        db.add_all([first, second])
        db.flush()
        apply_successful_payment(db, first, "evt_s1", {"type": "checkout.session.completed"})
        apply_successful_payment(db, second, "evt_s2", {"event": "charge.completed"})
        db.commit()
        active = db.query(Subscription).filter(Subscription.user_id == user.id, Subscription.status == "active").all()
        assert len(active) == 1
        cancelled = db.query(Subscription).filter(Subscription.user_id == user.id, Subscription.status == "cancelled").count()
        assert cancelled == 0
    finally:
        db.close()
