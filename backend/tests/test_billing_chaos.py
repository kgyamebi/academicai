"""Failure-injection on the billing path — crash, timeout, webhook burst."""

from __future__ import annotations

import random

from fastapi import HTTPException
import httpx
import pytest

from app.db.session import SessionLocal
from app.models.admin import WebhookEvent
from app.models.billing import Payment, PaymentTransaction
from app.models.user import User
from app.services.billing import (
    _pending_payment,
    apply_successful_payment,
    mark_webhook_processed,
    record_ambiguous_charge,
    record_webhook_event,
)
from app.services.billing_reconcile import reconcile_against_provider_snapshot
from app.services.credits import available_credits


def test_crash_after_db_write_before_ack_replay_is_idempotent(client):
    db = SessionLocal()
    try:
        user = User(email="chaos-ack@example.com", password_hash="x", full_name="C", is_guest=False)
        db.add(user)
        db.flush()
        payment = _pending_payment(
            db, user, "stripe", 299, "USD", "credits", f"chaos-ack:{user.id}", {"credits": 10, "pack": "credits_10"}
        )
        event_id = "evt_crash_before_ack"
        payload = b"{}"
        assert record_webhook_event(db, "stripe", event_id, "checkout.session.completed", payload, mark_processed=False)
        apply_successful_payment(db, payment, event_id, {"type": "checkout.session.completed"})
        db.commit()
        row = db.query(WebhookEvent).filter(WebhookEvent.event_id == event_id).one()
        assert row.processed_at is None
        credits = float(available_credits(db, user))
        # Restart replay
        assert record_webhook_event(db, "stripe", event_id, "checkout.session.completed", payload, mark_processed=False)
        apply_successful_payment(db, db.get(Payment, payment.id), event_id, {"type": "checkout.session.completed"})
        mark_webhook_processed(db, event_id)
        db.commit()
        assert float(available_credits(db, user)) == credits == 10
        assert db.query(PaymentTransaction).filter(PaymentTransaction.provider_event_id == event_id).count() == 1
        assert db.query(WebhookEvent).filter(WebhookEvent.event_id == event_id).one().processed_at is not None
    finally:
        db.close()


def test_ack_without_apply_is_detected_as_gap_on_restart(client):
    """Before-DB-write / after-ack: processed flag must not imply success."""
    db = SessionLocal()
    try:
        user = User(email="chaos-early-ack@example.com", password_hash="x", full_name="C", is_guest=False)
        db.add(user)
        db.flush()
        payment = _pending_payment(
            db, user, "stripe", 299, "USD", "credits", f"chaos-early:{user.id}", {"credits": 10, "pack": "credits_10"}
        )
        event_id = "evt_early_ack"
        record_webhook_event(db, "stripe", event_id, "checkout.session.completed", b"{}", mark_processed=True)
        db.commit()
        assert payment.status == "pending"
        assert float(available_credits(db, user)) == 0
        replay = record_webhook_event(db, "stripe", event_id, "checkout.session.completed", b"{}", mark_processed=False)
        assert replay is False
        # Operator path: payment still pending; reconcile snapshot will miss provider success until repaired.
        snapshot = [{"provider": "stripe", "provider_payment_id": event_id, "amount_cents": 299, "currency": "USD", "status": "successful"}]
        report = reconcile_against_provider_snapshot(db, snapshot)
        assert report["ok"] is False
        kinds = {m["kind"] for m in report["mismatches"]}
        assert "missing_internal" in kinds or "status_mismatch" in kinds
    finally:
        db.close()


def test_processor_timeout_leaves_charge_unknown_never_assumes(client):
    db = SessionLocal()
    try:
        user = User(email="chaos-timeout@example.com", password_hash="x", full_name="C", is_guest=False)
        db.add(user)
        db.flush()
        payment = _pending_payment(
            db, user, "stripe", 199, "USD", "subscription", f"chaos-to:{user.id}", {"plan": "student"}
        )
        db.commit()
        from app.services.billing import _raise_provider_error

        with pytest.raises(HTTPException) as ei:
            _raise_provider_error(db, payment, "stripe", httpx.TimeoutException("stripe timed out"), "fail")
        assert ei.value.status_code == 503
        db.commit()
        db.refresh(payment)
        assert payment.status == "pending"
        unknown = (
            db.query(PaymentTransaction)
            .filter(
                PaymentTransaction.payment_id == payment.id,
                PaymentTransaction.event_type == "charge.unknown",
            )
            .one()
        )
        assert unknown.status == "unknown"
        report = reconcile_against_provider_snapshot(db, [])
        assert any(m["kind"] == "charge_unknown" for m in report["mismatches"])
    finally:
        db.close()


def test_record_ambiguous_charge_is_idempotent(client):
    db = SessionLocal()
    try:
        user = User(email="chaos-unknown-id@example.com", password_hash="x", full_name="C", is_guest=False)
        db.add(user)
        db.flush()
        payment = _pending_payment(db, user, "paystack", 199, "USD", "subscription", f"unk:{user.id}", {"plan": "student"})
        record_ambiguous_charge(db, payment, reason="timeout")
        record_ambiguous_charge(db, payment, reason="timeout again")
        db.commit()
        assert (
            db.query(PaymentTransaction)
            .filter(PaymentTransaction.event_type == "charge.unknown", PaymentTransaction.payment_id == payment.id)
            .count()
            == 1
        )
        assert payment.status == "pending"
    finally:
        db.close()


def test_backlogged_webhook_burst_dedup_and_order(client):
    db = SessionLocal()
    try:
        user = User(email="chaos-burst@example.com", password_hash="x", full_name="C", is_guest=False)
        db.add(user)
        db.flush()
        payment = _pending_payment(
            db, user, "stripe", 299, "USD", "credits", f"burst:{user.id}", {"credits": 10, "pack": "credits_10"}
        )
        db.commit()
        events = [
            ("evt_burst_ok", "checkout.session.completed", lambda: apply_successful_payment(db, payment, "evt_burst_ok", {"type": "checkout.session.completed"})),
            ("evt_burst_ok", "checkout.session.completed", lambda: apply_successful_payment(db, db.get(Payment, payment.id), "evt_burst_ok", {"type": "checkout.session.completed"})),
            ("evt_burst_ok_dup", "checkout.session.completed", lambda: apply_successful_payment(db, db.get(Payment, payment.id), "evt_burst_ok_dup", {"type": "checkout.session.completed"})),
        ]
        # Simulate hours-later burst: shuffled deliveries including duplicates.
        random.seed(17)
        order = [0, 1, 2, 0, 2, 1]
        random.shuffle(order)
        for idx in order:
            event_id, event_type, apply = events[idx]
            payload = event_id.encode()
            should = record_webhook_event(db, "stripe", event_id, event_type, payload, mark_processed=False)
            if should:
                apply()
                mark_webhook_processed(db, event_id)
            db.commit()
        assert float(available_credits(db, user)) == 10
        assert db.get(Payment, payment.id).status == "successful"
        assert db.query(PaymentTransaction).filter(PaymentTransaction.payment_id == payment.id, PaymentTransaction.event_type == "payment.successful").count() == 1
    finally:
        db.close()
