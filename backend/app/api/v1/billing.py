from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.time import utcnow
from app.db.session import get_db
from app.deps import get_current_user
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
    payment_from_metadata,
    record_webhook_event,
    verify_flutterwave_signature,
    verify_paystack_signature,
    verify_stripe_signature,
)
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
def checkout(payload: CheckoutIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    result = create_checkout(db, user, payload.plan_slug, payload.provider, payload.currency)
    db.commit()
    return result


@router.post("/credits")
def buy_credits(payload: CreditPurchaseIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
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
    if not event_id or not record_webhook_event(db, "stripe", event_id, event_type, payload):
        db.commit()
        return {"received": True, "duplicate": True}
    obj = event.get("data", {}).get("object", {})
    payment = payment_from_metadata(db, obj.get("metadata"))
    if event_type in {"checkout.session.completed", "invoice.paid", "payment_intent.succeeded"} and payment:
        apply_successful_payment(db, payment, event_id, event)
    elif event_type in {"invoice.payment_failed", "payment_intent.payment_failed"} and payment:
        mark_payment_failed(db, payment, event_id, event)
    elif event_type in {"charge.refunded", "charge.refund.updated", "refund.created"} and payment:
        amount = obj.get("amount_refunded") or obj.get("amount")
        apply_refund(db, payment, event_id, event, amount_cents=int(amount) if amount is not None else None)
    elif event_type in {"checkout.session.expired", "checkout.session.async_payment_failed"} and payment:
        mark_payment_cancelled(db, payment, event_id, event)
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
    if not event_id or not record_webhook_event(db, "paystack", f"paystack:{event_id}:{event_type}", event_type, payload):
        db.commit()
        return {"received": True, "duplicate": True}
    payment = db.get(Payment, event_id) if _is_uuid(event_id) else None
    if not payment:
        payment = payment_from_metadata(db, (data.get("metadata") or {}))
    if event_type == "charge.success" and payment:
        apply_successful_payment(db, payment, event_id, event)
    elif event_type in {"charge.failed", "charge.abandoned"} and payment:
        mark_payment_failed(db, payment, event_id, event)
    elif event_type in {"refund.processed", "charge.refunded"} and payment:
        apply_refund(db, payment, event_id, event)
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
    if not event_id or not record_webhook_event(db, "flutterwave", f"flw:{event_id}", event_type, payload):
        db.commit()
        return {"received": True, "duplicate": True}
    tx_ref = str(data.get("tx_ref") or "")
    payment = db.get(Payment, tx_ref) if _is_uuid(tx_ref) else None
    if not payment:
        payment = payment_from_metadata(db, data.get("meta") or {})
    status_value = str(data.get("status") or "").lower()
    if status_value == "successful" and payment:
        apply_successful_payment(db, payment, event_id, event)
    elif status_value == "failed" and payment:
        mark_payment_failed(db, payment, event_id, event)
    elif status_value == "cancelled" and payment:
        mark_payment_cancelled(db, payment, event_id, event)
    elif status_value == "refunded" and payment:
        apply_refund(db, payment, event_id, event)
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
    db.commit()
    return {"status": sub.status, "cancel_at_period_end": True}


def _is_uuid(value: str) -> bool:
    from uuid import UUID

    try:
        UUID(value)
        return True
    except ValueError:
        return False
