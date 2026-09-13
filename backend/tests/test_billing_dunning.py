"""Dunning / failed-payment recovery — sandbox only."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

from fastapi import HTTPException

from app.db.session import SessionLocal
from app.models.billing import Payment, PaymentTransaction, Plan, Subscription
from app.models.user import User
from app.services.billing import _pending_payment, apply_successful_payment, mark_payment_failed
from app.services.dunning import (
    MAX_ATTEMPTS,
    recover_by_payment_method_update,
    record_failed_renewal,
    retry_idempotency_key,
    schedule_retry_payment,
)
from app.services.subscription_fsm import assert_initial_status


def _user_and_plan(db, email: str) -> tuple[User, Plan]:
    user = User(email=email, password_hash="x", full_name="Dunning", is_guest=False)
    db.add(user)
    db.flush()
    plan = db.query(Plan).filter(Plan.slug == "student").one()
    return user, plan


def _active_sub(db, user: User, plan: Plan) -> Subscription:
    sub = Subscription(
        user_id=user.id,
        plan_id=plan.id,
        status=assert_initial_status("active"),
        provider="stripe",
    )
    db.add(sub)
    db.flush()
    return sub


def test_failed_renewal_enters_past_due_and_schedules_retry(client):
    db = SessionLocal()
    try:
        user, plan = _user_and_plan(db, "dunning-retry@example.com")
        sub = _active_sub(db, user, plan)
        result = record_failed_renewal(db, sub)
        db.commit()
        assert result["outcome"] == "scheduled_retry"
        assert result["attempts"] == 1
        assert result["retry_key"] == retry_idempotency_key(sub)
        assert sub.status == "past_due"
        payment = schedule_retry_payment(db, user, sub, provider="stripe", amount_cents=199)
        db.commit()
        assert payment.idempotency_key == result["retry_key"]
        assert payment.status == "pending"
    finally:
        db.close()


def test_retry_exhaustion_cancels_subscription(client):
    db = SessionLocal()
    try:
        user, plan = _user_and_plan(db, "dunning-exhaust@example.com")
        sub = _active_sub(db, user, plan)
        for i in range(MAX_ATTEMPTS):
            result = record_failed_renewal(db, sub)
        db.commit()
        assert result["outcome"] == "cancelled"
        assert result["attempts"] == MAX_ATTEMPTS
        assert sub.status == "cancelled"
        assert result["retry_key"] is None
    finally:
        db.close()


def test_payment_method_update_recovers_before_exhaustion(client):
    db = SessionLocal()
    try:
        user, plan = _user_and_plan(db, "dunning-pm@example.com")
        sub = _active_sub(db, user, plan)
        record_failed_renewal(db, sub)
        db.commit()
        assert sub.status == "past_due"
        recover_by_payment_method_update(
            db, user, sub, provider="stripe", amount_cents=199, event_id="evt_pm_recover"
        )
        db.commit()
        db.refresh(sub)
        assert sub.status == "active"
        assert sub.dunning_attempts == 0
        assert db.query(Subscription).filter(Subscription.user_id == user.id, Subscription.status == "active").count() == 1
    finally:
        db.close()


def test_invoice_failed_webhook_starts_dunning_without_subscription_id(client):
    db = SessionLocal()
    try:
        user, plan = _user_and_plan(db, "dunning-invoice@example.com")
        sub = _active_sub(db, user, plan)
        payment = _pending_payment(
            db, user, "stripe", 199, "USD", "subscription", f"invfail:{user.id}", {"plan": "student"}
        )
        mark_payment_failed(db, payment, "evt_inv_fail", {"type": "invoice.payment_failed"})
        db.commit()
        db.refresh(sub)
        assert sub.status == "past_due"
        assert sub.dunning_attempts == 1
        assert payment.subscription_id == sub.id
    finally:
        db.close()


def test_successful_retry_does_not_double_bill_on_race(client):
    db = SessionLocal()
    try:
        user, plan = _user_and_plan(db, "dunning-race@example.com")
        sub = _active_sub(db, user, plan)
        record_failed_renewal(db, sub)
        db.commit()
        sub_id = sub.id
        user_id = user.id
    finally:
        db.close()

    def _fire(event_id: str) -> None:
        local = SessionLocal()
        try:
            u = local.get(User, user_id)
            s = local.get(Subscription, sub_id)
            try:
                pay = schedule_retry_payment(local, u, s, provider="stripe", amount_cents=199)
            except HTTPException:
                from sqlalchemy import select

                pay = local.scalar(select(Payment).where(Payment.idempotency_key == retry_idempotency_key(s)))
            apply_successful_payment(local, pay, event_id, {"type": "invoice.paid", "dunning_recovery": True})
            local.commit()
        finally:
            local.close()

    with ThreadPoolExecutor(max_workers=2) as pool:
        futs = [pool.submit(_fire, "evt_race_a"), pool.submit(_fire, "evt_race_b")]
        for fut in futs:
            fut.result()

    db = SessionLocal()
    try:
        active = db.query(Subscription).filter(Subscription.user_id == user_id, Subscription.status == "active").all()
        assert len(active) == 1
        assert active[0].id == sub_id
        payments = db.query(Payment).filter(Payment.user_id == user_id, Payment.purpose == "subscription").all()
        successful = [p for p in payments if p.status == "successful"]
        assert len(successful) == 1
        assert db.query(PaymentTransaction).filter(PaymentTransaction.event_type == "payment.successful").count() == 1
    finally:
        db.close()
