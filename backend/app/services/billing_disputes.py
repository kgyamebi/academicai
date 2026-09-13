"""Chargeback / dispute lifecycle. Credits stay until the dispute is lost."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.time import utcnow
from app.models.billing import Payment, PaymentTransaction, Subscription
from app.services.subscription_fsm import apply_status


def open_dispute(db: Session, payment: Payment, provider_event_id: str, payload: dict) -> None:
    existing = db.scalar(select(PaymentTransaction).where(PaymentTransaction.provider_event_id == provider_event_id))
    if existing:
        return
    payment.status = "disputed"
    db.add(
        PaymentTransaction(
            payment_id=payment.id,
            event_type="payment.disputed",
            provider_event_id=provider_event_id,
            status="disputed",
            payload=payload,
        )
    )
    sub = _subscription_for_payment(db, payment)
    if sub and sub.status in {"active", "past_due", "trialing"}:
        apply_status(sub, "suspended")
        sub.disputed_at = utcnow()
    from app.services.billing_audit import append_audit

    append_audit(
        db,
        event_type="payment.disputed",
        entity_type="payment",
        entity_id=str(payment.id),
        payload={"provider_event_id": provider_event_id},
    )


def resolve_dispute(
    db: Session,
    payment: Payment,
    provider_event_id: str,
    payload: dict,
    *,
    won: bool,
) -> None:
    existing = db.scalar(select(PaymentTransaction).where(PaymentTransaction.provider_event_id == provider_event_id))
    if existing:
        return
    sub = _subscription_for_payment(db, payment)
    if won:
        payment.status = "successful"
        db.add(
            PaymentTransaction(
                payment_id=payment.id,
                event_type="payment.dispute_won",
                provider_event_id=provider_event_id,
                status="successful",
                payload=payload,
            )
        )
        if sub and sub.status == "suspended":
            apply_status(sub, "active")
            sub.disputed_at = None
        from app.services.billing_audit import append_audit

        append_audit(
            db,
            event_type="payment.dispute_won",
            entity_type="payment",
            entity_id=str(payment.id),
            payload={"provider_event_id": provider_event_id},
        )
        return
    from app.services.billing import apply_refund

    apply_refund(db, payment, provider_event_id, payload)
    if sub and sub.status in {"suspended", "active", "past_due"}:
        apply_status(sub, "cancelled")
        sub.cancelled_at = utcnow()


def _subscription_for_payment(db: Session, payment: Payment) -> Subscription | None:
    if payment.subscription_id:
        return db.get(Subscription, payment.subscription_id)
    if payment.purpose != "subscription":
        return None
    return db.scalar(
        select(Subscription)
        .where(
            Subscription.user_id == payment.user_id,
            Subscription.status.in_(("active", "past_due", "suspended", "trialing")),
            Subscription.provider == payment.provider,
        )
        .order_by(Subscription.created_at.desc())
    )
