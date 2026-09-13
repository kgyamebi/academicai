"""Append-only hash-chained financial audit trail."""

from __future__ import annotations

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError, OperationalError

from app.db.session import SessionLocal
from app.models.billing import FinancialAuditEntry, Payment
from app.models.user import User
from app.services.billing import apply_successful_payment
from app.services.billing_audit import append_audit, install_append_only_guards, verify_chain


def test_hash_chain_links_successive_entries(client):
    db = SessionLocal()
    try:
        first = append_audit(
            db, event_type="payment.successful", entity_type="payment", entity_id="a", payload={"n": 1}
        )
        second = append_audit(
            db, event_type="payment.failed", entity_type="payment", entity_id="b", payload={"n": 2}
        )
        db.commit()
        assert second.prev_hash == first.entry_hash
        assert first.prev_hash == "0" * 64
        assert verify_chain(db) is True
    finally:
        db.close()


def test_tampered_payload_hash_breaks_chain(client):
    db = SessionLocal()
    try:
        append_audit(db, event_type="payment.successful", entity_type="payment", entity_id="x")
        row = append_audit(db, event_type="payment.refunded", entity_type="payment", entity_id="y")
        db.commit()
        row.payload_hash = "deadbeef" * 8
        db.flush()
        assert verify_chain(db) is False
        db.rollback()
    finally:
        db.close()


def test_update_and_delete_of_audit_row_are_rejected(client):
    db = SessionLocal()
    try:
        install_append_only_guards(db)
        entry = append_audit(db, event_type="payment.successful", entity_type="payment", entity_id="z")
        db.commit()
        with pytest.raises((IntegrityError, OperationalError)):
            db.execute(text("UPDATE financial_audit_entries SET event_type = 'tampered'"))
            db.commit()
        db.rollback()
        with pytest.raises((IntegrityError, OperationalError)):
            db.execute(text("DELETE FROM financial_audit_entries"))
            db.commit()
        db.rollback()
        remaining = db.query(FinancialAuditEntry).filter(FinancialAuditEntry.id == entry.id).one()
        assert remaining.event_type == "payment.successful"
    finally:
        db.close()


def test_successful_payment_appends_audit_entry(client):
    db = SessionLocal()
    try:
        user = User(email="audit-pay@example.com", password_hash="x", full_name="A", is_guest=False)
        db.add(user)
        db.flush()
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
        db.flush()
        apply_successful_payment(db, payment, "evt_audit", {"ok": True})
        db.commit()
        rows = db.query(FinancialAuditEntry).filter(FinancialAuditEntry.entity_id == str(payment.id)).all()
        assert any(r.event_type == "payment.successful" for r in rows)
        assert verify_chain(db) is True
    finally:
        db.close()
