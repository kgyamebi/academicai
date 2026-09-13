"""Failed-payment dunning: 3 attempts then cancel. Idempotent retries."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.time import utcnow
from app.models.billing import Payment, Plan, Subscription
from app.models.user import User
from app.services.subscription_fsm import apply_status

MAX_ATTEMPTS = 3


def retry_idempotency_key(subscription: Subscription) -> str:
    return f"dunning:{subscription.id}:{int(subscription.dunning_attempts or 0)}"


def record_failed_renewal(db: Session, subscription: Subscription) -> dict:
    apply_status(subscription, "past_due")
    subscription.dunning_attempts = int(subscription.dunning_attempts or 0) + 1
    if subscription.dunning_attempts >= MAX_ATTEMPTS:
        apply_status(subscription, "cancelled")
        subscription.cancelled_at = utcnow()
        return {
            "outcome": "cancelled",
            "attempts": subscription.dunning_attempts,
            "retry_key": None,
        }
    return {
        "outcome": "scheduled_retry",
        "attempts": subscription.dunning_attempts,
        "retry_key": retry_idempotency_key(subscription),
    }


def recover_dunning(db: Session, subscription: Subscription) -> None:
    apply_status(subscription, "active")
    subscription.dunning_attempts = 0
    subscription.disputed_at = None


def schedule_retry_payment(
    db: Session,
    user: User,
    subscription: Subscription,
    *,
    provider: str,
    amount_cents: int,
) -> Payment:
    from app.services.billing import _pending_payment

    plan = db.get(Plan, subscription.plan_id)
    slug = plan.slug if plan else "unknown"
    payment = _pending_payment(
        db,
        user,
        provider,
        amount_cents,
        "USD",
        "subscription",
        retry_idempotency_key(subscription),
        {"plan": slug, "dunning": True, "logical_purchase_id": retry_idempotency_key(subscription)},
    )
    payment.subscription_id = subscription.id
    db.flush()
    return payment


def recover_by_payment_method_update(
    db: Session,
    user: User,
    subscription: Subscription,
    *,
    provider: str,
    amount_cents: int,
    event_id: str,
) -> Payment:
    """Customer updates card mid-dunning: one retry payment, then success."""
    payment = schedule_retry_payment(db, user, subscription, provider=provider, amount_cents=amount_cents)
    from app.services.billing import apply_successful_payment

    apply_successful_payment(db, payment, event_id, {"type": "invoice.paid", "dunning_recovery": True})
    return payment
