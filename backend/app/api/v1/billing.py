from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.deps import get_current_user
from app.models.billing import Credit, Payment, Plan, Subscription
from app.models.user import User
from app.schemas.common import CheckoutIn, CreditPurchaseIn
from app.services.billing import (
    CREDIT_PACKS,
    apply_successful_payment,
    create_checkout,
    list_plans,
    localize_price,
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
        "plan": {"slug": plan.slug, "name": plan.name, "checks_per_month": plan.checks_per_month, "max_words": plan.max_words, "features": features_for(plan)},
        "subscription": {
            "status": sub.status if sub else "none",
            "checks_used": sub.checks_used if sub else 0,
            "period_end": sub.current_period_end.isoformat() if sub and sub.current_period_end else None,
        },
        "credits": float(wallet.remaining) if wallet else 0,
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
    payment = Payment(
        user_id=user.id,
        provider=payload.provider,
        amount_cents=pack["price_usd_cents"],
        currency=payload.currency.upper(),
        status="pending",
        purpose="credits",
        raw_payload={"credits": pack["credits"], "pack": pack["id"]},
    )
    db.add(payment)
    db.commit()
    return {"payment_id": str(payment.id), "status": "pending", "message": "Credits are added only after a verified webhook."}


@router.post("/payments/webhook")
async def stripe_webhook(
    request: Request,
    stripe_signature: str | None = Header(default=None, alias="Stripe-Signature"),
    db: Session = Depends(get_db),
):
    payload = await request.body()
    if not stripe_signature:
        raise HTTPException(400, "Missing signature.")
    event = verify_stripe_signature(payload, stripe_signature)
    provider_id = str(event.get("id") or event.get("data", {}).get("object", {}).get("id"))
    obj = event.get("data", {}).get("object", {})
    payment_id = (obj.get("metadata") or {}).get("payment_id")
    payment = db.get(Payment, payment_id) if payment_id else None
    if payment:
        apply_successful_payment(db, payment, provider_id, event)
        db.commit()
    return {"received": True}


@router.post("/{subscription_id}/cancel")
def cancel_subscription(subscription_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    from datetime import UTC, datetime
    from uuid import UUID

    sub = db.get(Subscription, UUID(subscription_id))
    if not sub or sub.user_id != user.id:
        raise HTTPException(404, "Subscription not found.")
    sub.cancel_at_period_end = True
    sub.cancelled_at = datetime.now(UTC)
    db.commit()
    return {"status": sub.status, "cancel_at_period_end": True}
