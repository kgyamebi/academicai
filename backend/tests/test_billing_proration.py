"""Proration math — integer cents, non-round cycle boundaries."""

from __future__ import annotations

from datetime import timedelta

import pytest
from fastapi import HTTPException

from app.core.time import utcnow
from app.db.session import SessionLocal
from app.models.billing import Plan, Subscription
from app.models.user import User
from app.services.billing import _pending_payment, apply_successful_payment
from app.services.proration import apply_plan_change, prorate_plan_change, remaining_days
from app.services.subscription_fsm import assert_initial_status


def test_remaining_days_day_17_of_30():
    assert remaining_days(day_index=17, cycle_days=30) == 13


def test_upgrade_student_to_pro_day_17_exact_cents():
    result = prorate_plan_change(old_cents=199, new_cents=399, day_index=17, cycle_days=30)
    assert result["remaining_days"] == 13
    assert result["unused_old_cents"] == 86
    assert result["unused_new_cents"] == 173
    assert result["charge_cents"] == 87
    assert result["credit_cents"] == 0
    assert result["upgrade"] is True
    assert result["deferred"] is False


def test_downgrade_is_deferred_no_immediate_credit():
    result = prorate_plan_change(old_cents=399, new_cents=199, day_index=17, cycle_days=30)
    assert result["upgrade"] is False
    assert result["deferred"] is True
    assert result["charge_cents"] == 0
    assert result["credit_cents"] == 0


def test_apply_plan_change_stores_pending_plan_on_downgrade(client):
    db = SessionLocal()
    try:
        user = User(email="prorate@example.com", password_hash="x", full_name="P", is_guest=False)
        db.add(user)
        db.flush()
        student = db.query(Plan).filter(Plan.slug == "student").one()
        pro = db.query(Plan).filter(Plan.slug == "pro").one()
        sub = Subscription(
            user_id=user.id,
            plan_id=pro.id,
            status=assert_initial_status("active"),
            provider="stripe",
            current_period_start=utcnow(),
            current_period_end=utcnow() + timedelta(days=30),
        )
        db.add(sub)
        db.flush()
        result = apply_plan_change(sub, student, day_index=17, cycle_days=30)
        db.commit()
        assert result["deferred"] is True
        assert sub.pending_plan_id == student.id
        assert sub.plan_id == pro.id
    finally:
        db.close()


def test_cancel_then_resubscribe_same_month_is_rejected(client):
    db = SessionLocal()
    try:
        user = User(email="resub@example.com", password_hash="x", full_name="R", is_guest=False)
        db.add(user)
        db.flush()
        key = f"sub:{user.id}:student:{utcnow().strftime('%Y%m')}"
        first = _pending_payment(db, user, "stripe", 199, "USD", "subscription", key, {"plan": "student"})
        apply_successful_payment(db, first, "evt_first_month", {"type": "checkout.session.completed"})
        db.commit()
        with pytest.raises(HTTPException) as ei:
            _pending_payment(db, user, "stripe", 199, "USD", "subscription", key, {"plan": "student"})
        assert ei.value.status_code == 409
    finally:
        db.close()
