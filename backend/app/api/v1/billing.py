from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.metrics import incr
from app.core.rate_limit import check_rate_limit
from app.core.time import utcnow
from app.db.session import get_db
from app.deps import get_current_user
from app.config import get_settings
from app.models.billing import Credit, Payment, Subscription
from app.models.user import User
from app.schemas.common import CheckoutIn, CreditPurchaseIn
from app.services.billing import (
    CREDIT_PACKS,
    apply_refund,
    apply_successful_payment,
    create_checkout,
    create_credit_checkout,
    list_plans,
    localize_price,
    mark_payment_cancelled,
    mark_payment_failed,
    mark_webhook_processed,
    payment_from_dispute,
    payment_from_metadata,
    record_webhook_event,
    verify_flutterwave_signature,
    verify_paystack_signature,
    verify_stripe_signature,
)
from app.services.billing import _record_billing_analytics
from app.services.entitlements import current_subscription, features_for, plan_for

router = APIRouter(prefix="/api/billing", tags=["billing"])


@router.get("/plans")
def plans(currency: str = "USD", db: Session = Depends(get_db)):
    items = []
    for plan in list_plans(db):
        items.append(
            {
                "slug": plan.slug,
                "name": plan.name,
                "description": plan.description,
                "checks_per_month": plan.checks_per_month,
                "max_words": plan.max_words,
                "features": plan.features,
                "price": localize_price(plan.price_usd_cents, currency),
            }
        )
    return {"items": items, "credits": [{**p, "price": localize_price(p["price_usd_cents"], currency)} for p in CREDIT_PACKS]}


@router.get("")
def my_billing(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    plan = plan_for(db, user)
    sub, _ = current_subscription(db, user)
    wallet = db.scalar(select(Credit).where(Credit.user_id == user.id))
    settings = get_settings()
    checkout_available = bool(
        (settings.stripe_secret_key or "").strip()
        or (settings.paystack_secret_key or "").strip()
        or (settings.flutterwave_secret_key or "").strip()
    )
    return {
        "plan": {
            "slug": plan.slug,
            "name": plan.name,
            "checks_per_month": plan.checks_per_month,
            "max_words": plan.max_words,
            "features": features_for(plan),
        },
        "subscription": {
            "id": str(sub.id) if sub else None,
            "status": sub.status if sub else "none",
            "checks_used": sub.checks_used if sub else 0,
            "period_end": sub.current_period_end.isoformat() if sub and sub.current_period_end else None,
        },
        "credits": float(wallet.remaining) if wallet else 0,
        "checkout_available": checkout_available,
    }


@router.get("/payments")
def list_payments(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = db.scalars(select(Payment).where(Payment.user_id == user.id).order_by(Payment.created_at.desc()).limit(50)).all()
    return {
        "items": [
            {
                "id": str(p.id),
                "provider": p.provider,
                "amount_cents": p.amount_cents,
                "currency": p.currency,
                "status": p.status,
                "purpose": p.purpose,
            }
            for p in rows
        ]
    }


@router.get("/payments/{payment_id}")
def get_payment(payment_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    from uuid import UUID

    try:
        pid = UUID(payment_id)
    except ValueError as exc:
        raise HTTPException(404, "Payment not found.") from exc
    payment = db.get(Payment, pid)
    if not payment or payment.user_id != user.id:
        raise HTTPException(404, "Payment not found.")
    return {
        "id": str(payment.id),
        "provider": payment.provider,
        "amount_cents": payment.amount_cents,
        "currency": payment.currency,
        "status": payment.status,
        "purpose": payment.purpose,
    }


@router.post("/checkout")
def checkout(
    request: Request,
    payload: CheckoutIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    check_rate_limit(request, "checkout", user)
    from app.services.auth import assert_email_verified

    assert_email_verified(user)
    result = create_checkout(db, user, payload.plan_slug, payload.provider, payload.currency)
    db.commit()
    return result


@router.post("/credits")
def buy_credits(
    request: Request,
    payload: CreditPurchaseIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    check_rate_limit(request, "checkout", user)
    from app.services.auth import assert_email_verified

    assert_email_verified(user)
    pack = next((p for p in CREDIT_PACKS if p["id"] == payload.pack_id), None)
    if not pack:
        raise HTTPException(400, "Unknown credit pack.")
    result = create_credit_checkout(db, user, pack, payload.provider, payload.currency)
    db.commit()
    return result


@router.post("/payments/webhook")
@router.post("/webhooks/stripe")
async def stripe_webhook(
    request: Request,
    stripe_signature: str | None = Header(default=None, alias="Stripe-Signature"),
    db: Session = Depends(get_db),
):
    payload = await request.body()
    if not stripe_signature:
        raise HTTPException(400, "Missing signature.")
    event = verify_stripe_signature(payload, stripe_signature)
    event_id = str(event.get("id") or "")
    event_type = str(event.get("type") or "")
    if not event_id:
        raise HTTPException(400, "Missing webhook event id.")
    if not record_webhook_event(db, "stripe", event_id, event_type, payload, mark_processed=False):
        incr("billing.webhook_duplicates")
        db.commit()
        return {"received": True, "duplicate": True}
    obj = event.get("data", {}).get("object", {})
    payment = payment_from_metadata(db, obj.get("metadata"))
    actionable = event_type in {
        "checkout.session.completed",
        "invoice.paid",
        "payment_intent.succeeded",
        "invoice.payment_failed",
        "payment_intent.payment_failed",
        "charge.refunded",
        "charge.refund.updated",
        "refund.created",
        "checkout.session.expired",
        "checkout.session.async_payment_failed",
        "charge.dispute.created",
        "charge.dispute.updated",
        "charge.dispute.closed",
        "charge.dispute.funds_withdrawn",
        "charge.dispute.funds_reinstated",
    }
    if event_type.startswith("charge.dispute.") and not payment:
        payment = payment_from_dispute(db, obj)
    if actionable and not payment:
        incr("billing.webhook_unmatched")
        from app.core.alerting import notify_payment_failure

        notify_payment_failure(provider="stripe", reason="unmatched webhook payment", event_id=event_id)
        db.commit()
        raise HTTPException(503, "Payment not found for webhook. Retry later.")
    if event_type in {"checkout.session.completed", "invoice.paid", "payment_intent.succeeded"} and payment:
        apply_successful_payment(db, payment, event_id, event)
    elif event_type in {"invoice.payment_failed", "payment_intent.payment_failed"} and payment:
        mark_payment_failed(db, payment, event_id, event)
    elif event_type in {"charge.refunded", "charge.refund.updated", "refund.created"} and payment:
        amount = obj.get("amount_refunded") or obj.get("amount")
        applied = apply_refund(
            db, payment, event_id, event, amount_cents=int(amount) if amount is not None else None
        )
        if not applied:
            db.commit()
            raise HTTPException(503, "Refund deferred until payment succeeds. Retry later.")
    elif event_type in {"checkout.session.expired", "checkout.session.async_payment_failed"} and payment:
        mark_payment_cancelled(db, payment, event_id, event)
    elif event_type in {"charge.dispute.created", "charge.dispute.funds_withdrawn"} and payment:
        from app.services.billing_disputes import open_dispute

        open_dispute(db, payment, event_id, event)
    elif event_type in {"charge.dispute.closed", "charge.dispute.updated", "charge.dispute.funds_reinstated"} and payment:
        from app.services.billing_disputes import resolve_dispute

        status_value = str(obj.get("status") or "").lower()
        if status_value in {"needs_response", "warning_needs_response", "under_review"}:
            from app.services.billing_disputes import open_dispute

            open_dispute(db, payment, event_id, event)
        elif status_value in {"won", "warning_closed", "charge_refunded"}:
            resolve_dispute(db, payment, event_id, event, won=status_value != "charge_refunded")
        elif status_value in {"lost"}:
            resolve_dispute(db, payment, event_id, event, won=False)
    mark_webhook_processed(db, event_id)
    db.commit()
    return {"received": True}


@router.post("/webhooks/paystack")
async def paystack_webhook(
    request: Request,
    x_paystack_signature: str | None = Header(default=None, alias="x-paystack-signature"),
    db: Session = Depends(get_db),
):
    payload = await request.body()
    event = verify_paystack_signature(payload, x_paystack_signature)
    data = event.get("data") or {}
    event_id = str(data.get("reference") or event.get("id") or "")
    event_type = str(event.get("event") or "")
    stored_id = f"paystack:{event_id}:{event_type}"
    if not event_id:
        raise HTTPException(400, "Missing webhook event id.")
    if not record_webhook_event(db, "paystack", stored_id, event_type, payload, mark_processed=False):
        incr("billing.webhook_duplicates")
        db.commit()
        return {"received": True, "duplicate": True}
    payment = None
    if _is_uuid(event_id):
        from uuid import UUID

        payment = db.get(Payment, UUID(event_id))
    if not payment:
        payment = payment_from_metadata(db, (data.get("metadata") or {}))
    actionable = event_type in {
        "charge.success",
        "charge.failed",
        "charge.abandoned",
        "refund.processed",
        "charge.refunded",
        "charge.dispute.create",
        "charge.dispute.resolve",
    }
    if event_type.startswith("charge.dispute") and not payment:
        payment = payment_from_dispute(db, data)
    if actionable and not payment:
        incr("billing.webhook_unmatched")
        from app.core.alerting import notify_payment_failure

        notify_payment_failure(provider="paystack", reason="unmatched webhook payment", event_id=stored_id)
        db.commit()
        raise HTTPException(503, "Payment not found for webhook. Retry later.")
    if event_type == "charge.success" and payment:
        apply_successful_payment(db, payment, event_id, event)
    elif event_type in {"charge.failed", "charge.abandoned"} and payment:
        mark_payment_failed(db, payment, event_id, event)
    elif event_type in {"refund.processed", "charge.refunded"} and payment:
        amount = data.get("amount") or data.get("amount_refunded")
        applied = apply_refund(
            db, payment, event_id, event, amount_cents=int(amount) if amount is not None else None
        )
        if not applied:
            db.commit()
            raise HTTPException(503, "Refund deferred until payment succeeds. Retry later.")
    elif event_type == "charge.dispute.create" and payment:
        from app.services.billing_disputes import open_dispute

        open_dispute(db, payment, stored_id, event)
    elif event_type == "charge.dispute.resolve" and payment:
        from app.services.billing_disputes import resolve_dispute

        won = str((data.get("status") or event.get("status") or "")).lower() in {"won", "resolved", "merchant_won"}
        resolve_dispute(db, payment, stored_id, event, won=won)
    mark_webhook_processed(db, stored_id)
    db.commit()
    return {"received": True}


@router.post("/webhooks/flutterwave")
async def flutterwave_webhook(
    request: Request,
    verif_hash: str | None = Header(default=None, alias="verif-hash"),
    db: Session = Depends(get_db),
):
    payload = await request.body()
    event = verify_flutterwave_signature(payload, verif_hash)
    data = event.get("data") or {}
    event_id = str(data.get("id") or data.get("tx_ref") or "")
    event_type = str(event.get("event") or data.get("status") or "")
    stored_id = f"flw:{event_id}"
    if not event_id:
        raise HTTPException(400, "Missing webhook event id.")
    if not record_webhook_event(db, "flutterwave", stored_id, event_type, payload, mark_processed=False):
        incr("billing.webhook_duplicates")
        db.commit()
        return {"received": True, "duplicate": True}
    tx_ref = str(data.get("tx_ref") or "")
    payment = None
    if _is_uuid(tx_ref):
        from uuid import UUID

        payment = db.get(Payment, UUID(tx_ref))
    if not payment:
        payment = payment_from_metadata(db, data.get("meta") or {})
    if not payment:
        payment = payment_from_dispute(db, data)
    status_value = str(data.get("status") or "").lower()
    event_name = str(event.get("event") or "").lower()
    if (status_value in {"successful", "failed", "cancelled", "refunded"} or event_name.startswith("dispute")) and not payment:
        incr("billing.webhook_unmatched")
        from app.core.alerting import notify_payment_failure

        notify_payment_failure(provider="flutterwave", reason="unmatched webhook payment", event_id=stored_id)
        db.commit()
        raise HTTPException(503, "Payment not found for webhook. Retry later.")
    if event_name in {"dispute.created", "charge.dispute"} and payment:
        from app.services.billing_disputes import open_dispute

        open_dispute(db, payment, stored_id, event)
    elif event_name in {"dispute.resolved", "charge.dispute.resolved"} and payment:
        from app.services.billing_disputes import resolve_dispute

        won = str(data.get("status") or "").lower() in {"won", "resolved"}
        resolve_dispute(db, payment, stored_id, event, won=won)
    elif status_value == "successful" and payment:
        apply_successful_payment(db, payment, event_id, event)
    elif status_value == "failed" and payment:
        mark_payment_failed(db, payment, event_id, event)
    elif status_value == "cancelled" and payment:
        mark_payment_cancelled(db, payment, event_id, event)
    elif status_value == "refunded" and payment:
        applied = apply_refund(db, payment, event_id, event)
        if not applied:
            db.commit()
            raise HTTPException(503, "Refund deferred until payment succeeds. Retry later.")
    mark_webhook_processed(db, stored_id)
    db.commit()
    return {"received": True}


@router.post("/{subscription_id}/cancel")
def cancel_subscription(subscription_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    from uuid import UUID

    sub = db.get(Subscription, UUID(subscription_id))
    if not sub or sub.user_id != user.id:
        raise HTTPException(404, "Subscription not found.")
    sub.cancel_at_period_end = True
    sub.cancelled_at = utcnow()
    _record_billing_analytics(
        db,
        "subscription_cancelled",
        user_id=user.id,
        properties={"reason": "user_request", "subscription_id": str(sub.id)},
    )
    db.commit()
    return {"status": sub.status, "cancel_at_period_end": True}


def _is_uuid(value: str) -> bool:
    from uuid import UUID

    try:
        UUID(value)
        return True
    except ValueError:
        return False
