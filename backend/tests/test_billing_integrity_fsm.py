"""Billing integrity: FSM, webhook freshness, ledger drift fail-closed."""

from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

import pytest
from fastapi import HTTPException

from app.core.time import utcnow
from app.db.session import SessionLocal
from app.models.billing import Credit, Subscription
from app.models.user import User
from app.services import billing as billing_service
from app.services import credits as credits_service
from app.services.subscription_fsm import assert_transition, apply_status


def test_subscription_fsm_allows_active_to_cancelled():
    assert assert_transition("active", "cancelled") == "cancelled"


def test_subscription_fsm_rejects_cancelled_to_past_due():
    with pytest.raises(HTTPException) as ei:
        assert_transition("cancelled", "past_due")
    assert ei.value.status_code == 409


def test_subscription_fsm_apply_status(client):
    db = SessionLocal()
    try:
        user = User(email="fsm@example.com", password_hash="x", full_name="F", is_guest=False)
        db.add(user)
        db.flush()
        from app.services.auth import get_role
        from app.models.billing import Plan

        plan = db.query(Plan).first() or Plan(slug="free", name="Free", price_usd_cents=0)
        if plan.id is None:
            db.add(plan)
            db.flush()
        sub = Subscription(user_id=user.id, plan_id=plan.id, status="active", provider="stripe")
        db.add(sub)
        db.flush()
        apply_status(sub, "past_due")
        assert sub.status == "past_due"
        apply_status(sub, "cancelled")
        assert sub.status == "cancelled"
        with pytest.raises(HTTPException):
            apply_status(sub, "past_due")
        db.commit()
    finally:
        db.close()


def test_webhook_freshness_rejects_stale_paystack_event():
    old = (utcnow() - timedelta(hours=2)).isoformat()
    event = {"event": "charge.success", "data": {"paid_at": old, "reference": "x"}}
    with pytest.raises(HTTPException) as ei:
        billing_service.assert_webhook_event_freshness(event, provider="paystack")
    assert ei.value.status_code == 400


def test_webhook_freshness_allows_recent_event():
    recent = utcnow().isoformat()
    event = {"event": "charge.success", "data": {"paid_at": recent}}
    billing_service.assert_webhook_event_freshness(event, provider="paystack")


def test_webhook_freshness_allows_missing_timestamp():
    billing_service.assert_webhook_event_freshness({"event": "charge.success", "data": {}}, provider="paystack")


def test_grant_blocked_when_ledger_drift(client):
    db = SessionLocal()
    try:
        user = User(email="drift@example.com", password_hash="x", full_name="D", is_guest=False)
        db.add(user)
        db.flush()
        credits_service.grant_credits(db, user, Decimal("5"), "purchase")
        wallet = db.query(Credit).filter(Credit.user_id == user.id).one()
        wallet.remaining = Decimal("99")  # silent corruption
        db.flush()
        with pytest.raises(HTTPException) as ei:
            credits_service.grant_credits(db, user, Decimal("1"), "purchase")
        assert ei.value.status_code == 409
        db.rollback()
    finally:
        db.close()
