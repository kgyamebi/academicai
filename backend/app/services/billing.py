from __future__ import annotations

import hashlib
import hmac
import json
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.core.logging import get_logger
from app.models.billing import Credit, CreditTransaction, Payment, PaymentTransaction, Plan, Subscription
from app.models.user import User
from app.services.emailer import send_email

log = get_logger("billing")

CREDIT_PACKS = [
    {"id": "credits_10", "credits": 10, "price_usd_cents": 299, "label": "10 credits"},
    {"id": "credits_50", "credits": 50, "price_usd_cents": 999, "label": "50 credits"},
]

# Display FX is configuration, not business-logic conversion for charging.
DISPLAY_RATES = {
    "USD": 1,
    "GHS": 15.4,
    "NGN": 1600,
    "KES": 129,
    "ZAR": 18.2,
    "GBP": 0.78,
    "EUR": 0.92,
    "INR": 84,
    "CAD": 1.37,
    "AUD": 1.52,
    "AED": 3.67,
    "BRL": 5.6,
    "MXN": 18.5,
    "PHP": 58,
    "IDR": 16200,
    "THB": 36,
    "VND": 25400,
    "PKR": 278,
    "BDT": 121,
}

OPERATION_CREDITS = {
    "basic": Decimal("0"),
    "academic": Decimal("1"),
    "full": Decimal("2"),
    "rubric": Decimal("1"),
    "citation_verify": Decimal("0.5"),
    "coach": Decimal("0.25"),
    "compare": Decimal("1"),
}


def list_plans(db: Session) -> list[Plan]:
    return list(db.scalars(select(Plan).where(Plan.is_public.is_(True), Plan.is_active.is_(True)).order_by(Plan.sort_order)))


def localize_price(cents_usd: int, currency: str) -> dict:
    currency = currency.upper()
    rate = DISPLAY_RATES.get(currency, 1)
    # Display only — charging still happens in the provider's supported currency.
    major = round((cents_usd / 100) * rate, 2)
    return {"currency": currency, "amount": major, "usd_cents": cents_usd, "display_only": currency != "USD"}


def create_checkout(db: Session, user: User, plan_slug: str, provider: str, currency: str) -> dict:
    if user.is_guest:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Create an account to subscribe.")
    plan = db.scalar(select(Plan).where(Plan.slug == plan_slug, Plan.is_active.is_(True)))
    if not plan or plan.price_usd_cents <= 0:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "This plan cannot be purchased.")
    payment = Payment(
        user_id=user.id,
        provider=provider,
        amount_cents=plan.price_usd_cents,
        currency=currency.upper(),
        status="pending",
        purpose="subscription",
        idempotency_key=f"sub:{user.id}:{plan.slug}:{datetime.now(UTC).strftime('%Y%m')}",
        raw_payload={"plan": plan.slug},
    )
    db.add(payment)
    db.flush()
    settings = get_settings()
    if provider == "stripe" and settings.stripe_secret_key:
        return {"provider": "stripe", "payment_id": str(payment.id), "mode": "stripe_checkout"}
    # Development / adapter stub: mark as requiring webhook confirmation.
    return {
        "provider": provider,
        "payment_id": str(payment.id),
        "mode": "pending_provider",
        "message": "Complete payment with the configured provider. The account upgrades only after a verified webhook.",
    }


def apply_successful_payment(db: Session, payment: Payment, provider_event_id: str, payload: dict) -> None:
    existing = db.scalar(
        select(PaymentTransaction).where(PaymentTransaction.provider_event_id == provider_event_id)
    )
    if existing:
        return
    payment.status = "successful"
    db.add(
        PaymentTransaction(
            payment_id=payment.id,
            event_type="payment.successful",
            provider_event_id=provider_event_id,
            status="successful",
            payload=payload,
        )
    )
    user = db.get(User, payment.user_id)
    if payment.purpose == "subscription" and user:
        plan_slug = (payment.raw_payload or {}).get("plan")
        plan = db.scalar(select(Plan).where(Plan.slug == plan_slug))
        if plan:
            for sub in user.subscriptions:
                if sub.status == "active":
                    sub.status = "cancelled"
                    sub.cancelled_at = datetime.now(UTC)
            db.add(
                Subscription(
                    user_id=user.id,
                    plan_id=plan.id,
                    status="active",
                    provider=payment.provider,
                    current_period_start=datetime.now(UTC),
                    current_period_end=datetime.now(UTC) + timedelta(days=30),
                )
            )
            send_email(user.email, "Subscription confirmed", f"Your {plan.name} plan is now active.")
    if payment.purpose == "credits" and user:
        credits = Decimal(str((payment.raw_payload or {}).get("credits") or 0))
        wallet = db.scalar(select(Credit).where(Credit.user_id == user.id))
        if not wallet:
            wallet = Credit(user_id=user.id, remaining=Decimal("0"))
            db.add(wallet)
            db.flush()
        wallet.remaining = (wallet.remaining or Decimal("0")) + credits
        db.add(
            CreditTransaction(
                user_id=user.id,
                credit_id=wallet.id,
                amount=credits,
                status="available",
                operation="purchase",
            )
        )


def verify_stripe_signature(payload: bytes, signature: str) -> dict:
    settings = get_settings()
    if not settings.stripe_webhook_secret:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Stripe webhooks are not configured.")
    # Minimal Stripe-compatible check: stripe-signature t=...,v1=...
    parts = dict(item.split("=", 1) for item in signature.split(",") if "=" in item)
    timestamp = parts.get("t", "")
    expected = hmac.new(
        settings.stripe_webhook_secret.encode(),
        f"{timestamp}.".encode() + payload,
        hashlib.sha256,
    ).hexdigest()
    if not hmac.compare_digest(expected, parts.get("v1", "")):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid webhook signature.")
    return json.loads(payload.decode())


def consume_credits(db: Session, user: User, operation: str, job_id: UUID | None = None) -> None:
    amount = OPERATION_CREDITS.get(operation, Decimal("0"))
    if amount <= 0:
        return
    wallet = db.scalar(select(Credit).where(Credit.user_id == user.id))
    if not wallet or wallet.remaining < amount:
        return
    # Credits are optional top-up; subscriptions remain the primary entitlement.
    if job_id:
        prior = db.scalar(
            select(CreditTransaction).where(
                CreditTransaction.analysis_job_id == job_id,
                CreditTransaction.status == "consumed",
            )
        )
        if prior:
            return
    wallet.remaining -= amount
    db.add(
        CreditTransaction(
            user_id=user.id,
            credit_id=wallet.id,
            analysis_job_id=job_id,
            amount=amount,
            status="consumed",
            operation=operation,
        )
    )
