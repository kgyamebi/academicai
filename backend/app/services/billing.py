from __future__ import annotations

import hashlib
import hmac
import json
from datetime import timedelta
from decimal import Decimal
from uuid import UUID

import httpx
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.core.logging import get_logger
from app.core.security import constant_time_equals
from app.core.time import utcnow
from app.models.admin import WebhookEvent
from app.models.billing import Credit, CreditTransaction, Payment, PaymentTransaction, Plan, Subscription
from app.models.user import User
from app.services.emailer import send_email

log = get_logger("billing")

CREDIT_PACKS = [
    {"id": "credits_10", "credits": 10, "price_usd_cents": 299, "label": "10 credits"},
    {"id": "credits_50", "credits": 50, "price_usd_cents": 999, "label": "50 credits"},
]

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
    major = round((cents_usd / 100) * rate, 2)
    return {"currency": currency, "amount": major, "usd_cents": cents_usd, "display_only": currency != "USD"}


def create_checkout(db: Session, user: User, plan_slug: str, provider: str, currency: str) -> dict:
    if user.is_guest:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Create an account to subscribe.")
    plan = db.scalar(select(Plan).where(Plan.slug == plan_slug, Plan.is_active.is_(True)))
    if not plan or plan.price_usd_cents <= 0:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "This plan cannot be purchased.")
    payment = _pending_payment(
        db,
        user,
        provider,
        plan.price_usd_cents,
        currency,
        "subscription",
        f"sub:{user.id}:{plan.slug}:{utcnow().strftime('%Y%m')}",
        {"plan": plan.slug},
    )
    return _provider_checkout(db, user, payment, f"{plan.name} monthly", plan.price_usd_cents, currency, recurring=True)


def create_credit_checkout(db: Session, user: User, pack: dict, provider: str, currency: str) -> dict:
    if user.is_guest:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Create an account to buy credits.")
    payment = _pending_payment(
        db,
        user,
        provider,
        pack["price_usd_cents"],
        currency,
        "credits",
        f"credits:{user.id}:{pack['id']}:{utcnow().strftime('%Y%m%d%H')}",
        {"credits": pack["credits"], "pack": pack["id"]},
    )
    return _provider_checkout(db, user, payment, pack["label"], pack["price_usd_cents"], currency, recurring=False)


def apply_successful_payment(db: Session, payment: Payment, provider_event_id: str, payload: dict) -> None:
    existing = db.scalar(select(PaymentTransaction).where(PaymentTransaction.provider_event_id == provider_event_id))
    if existing:
        return
    if payment.status == "successful":
        return
    payment.status = "successful"
    payment.provider_payment_id = provider_event_id
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
                    sub.cancelled_at = utcnow()
            db.add(
                Subscription(
                    user_id=user.id,
                    plan_id=plan.id,
                    status="active",
                    provider=payment.provider,
                    current_period_start=utcnow(),
                    current_period_end=utcnow() + timedelta(days=30),
                )
            )
            send_email(user.email, "Subscription confirmed", f"Your {plan.name} plan is now active.")
    if payment.purpose == "credits" and user:
        from app.services.credits import grant_credits

        credits = Decimal(str((payment.raw_payload or {}).get("credits") or 0))
        if credits > 0:
            grant_credits(db, user, credits, "purchase")


def mark_payment_failed(db: Session, payment: Payment, provider_event_id: str, payload: dict) -> None:
    existing = db.scalar(select(PaymentTransaction).where(PaymentTransaction.provider_event_id == provider_event_id))
    if existing:
        return
    payment.status = "failed"
    db.add(
        PaymentTransaction(
            payment_id=payment.id,
            event_type="payment.failed",
            provider_event_id=provider_event_id,
            status="failed",
            payload=payload,
        )
    )
    if payment.subscription_id:
        sub = db.get(Subscription, payment.subscription_id)
        if sub:
            sub.status = "past_due"


def record_webhook_event(db: Session, provider: str, event_id: str, event_type: str, payload: bytes) -> bool:
    """Return True if this event is new and should be processed."""
    existing = db.scalar(select(WebhookEvent).where(WebhookEvent.event_id == event_id))
    if existing:
        return False
    db.add(
        WebhookEvent(
            provider=provider,
            event_id=event_id,
            event_type=event_type,
            payload_hash=hashlib.sha256(payload).hexdigest(),
            processed_at=utcnow(),
        )
    )
    db.flush()
    return True


def verify_stripe_signature(payload: bytes, signature: str) -> dict:
    settings = get_settings()
    if not settings.stripe_webhook_secret:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Stripe webhooks are not configured.")
    try:
        import stripe

        event = stripe.Webhook.construct_event(
            payload,
            signature,
            settings.stripe_webhook_secret,
            tolerance=settings.webhook_tolerance_seconds,
        )
        return event if isinstance(event, dict) else event.to_dict()
    except ImportError:
        return _stripe_hmac(payload, signature, settings.stripe_webhook_secret, settings.webhook_tolerance_seconds)
    except Exception as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid Stripe webhook signature.") from exc


def verify_paystack_signature(payload: bytes, signature: str | None) -> dict:
    settings = get_settings()
    secret = settings.paystack_webhook_secret or settings.paystack_secret_key
    if not secret:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Paystack webhooks are not configured.")
    if not signature:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Missing Paystack signature.")
    expected = hmac.new(secret.encode(), payload, hashlib.sha512).hexdigest()
    if not constant_time_equals(expected, signature):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid Paystack webhook signature.")
    return json.loads(payload.decode())


def verify_flutterwave_signature(payload: bytes, signature: str | None) -> dict:
    settings = get_settings()
    secret = settings.flutterwave_webhook_hash
    if not secret:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Flutterwave webhooks are not configured.")
    if not signature or not constant_time_equals(secret, signature):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid Flutterwave webhook signature.")
    return json.loads(payload.decode())


def payment_from_metadata(db: Session, metadata: dict | None) -> Payment | None:
    payment_id = (metadata or {}).get("payment_id")
    if not payment_id:
        return None
    try:
        return db.get(Payment, UUID(str(payment_id)))
    except (ValueError, TypeError):
        return None


def _pending_payment(
    db: Session,
    user: User,
    provider: str,
    amount_cents: int,
    currency: str,
    purpose: str,
    idempotency_key: str,
    raw_payload: dict,
) -> Payment:
    existing = db.scalar(select(Payment).where(Payment.idempotency_key == idempotency_key))
    if existing and existing.status == "pending":
        return existing
    if existing and existing.status == "successful":
        raise HTTPException(status.HTTP_409_CONFLICT, "This purchase was already completed.")
    payment = Payment(
        user_id=user.id,
        provider=provider,
        amount_cents=amount_cents,
        currency=currency.upper(),
        status="pending",
        purpose=purpose,
        idempotency_key=idempotency_key,
        raw_payload=raw_payload,
    )
    db.add(payment)
    db.flush()
    return payment


def _provider_checkout(
    db: Session,
    user: User,
    payment: Payment,
    label: str,
    amount_cents: int,
    currency: str,
    *,
    recurring: bool,
) -> dict:
    settings = get_settings()
    provider = payment.provider
    if provider == "stripe":
        url = _stripe_checkout(user, payment, label, amount_cents, currency, recurring)
        return {"provider": "stripe", "payment_id": str(payment.id), "checkout_url": url, "mode": "stripe_checkout"}
    if provider == "paystack":
        url = _paystack_checkout(user, payment, label, amount_cents, currency)
        return {"provider": "paystack", "payment_id": str(payment.id), "checkout_url": url, "mode": "paystack_checkout"}
    if provider == "flutterwave":
        url = _flutterwave_checkout(user, payment, label, amount_cents, currency)
        return {
            "provider": "flutterwave",
            "payment_id": str(payment.id),
            "checkout_url": url,
            "mode": "flutterwave_checkout",
        }
    raise HTTPException(status.HTTP_400_BAD_REQUEST, "Unsupported payment provider.")


def _stripe_checkout(user: User, payment: Payment, label: str, amount_cents: int, currency: str, recurring: bool) -> str:
    settings = get_settings()
    if not settings.stripe_secret_key:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Stripe is not configured.")
    try:
        import stripe

        stripe.api_key = settings.stripe_secret_key
        price_data = {
            "currency": currency.lower(),
            "unit_amount": amount_cents if currency.upper() == "USD" else amount_cents,
            "product_data": {"name": label},
        }
        if recurring:
            price_data["recurring"] = {"interval": "month"}
        session = stripe.checkout.Session.create(
            mode="subscription" if recurring else "payment",
            success_url=f"{settings.app_web_url}/app/billing?status=success&session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{settings.app_web_url}/app/billing?status=cancelled",
            client_reference_id=str(user.id),
            customer_email=user.email,
            line_items=[{"price_data": price_data, "quantity": 1}],
            metadata={"payment_id": str(payment.id), "user_id": str(user.id)},
            subscription_data={"metadata": {"payment_id": str(payment.id)}} if recurring else None,
            idempotency_key=payment.idempotency_key,
        )
        if not session.url:
            raise HTTPException(status.HTTP_502_BAD_GATEWAY, "Stripe did not return a checkout URL.")
        return session.url
    except HTTPException:
        raise
    except Exception as exc:
        log.error("stripe_checkout_failed", error=str(exc))
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, "Could not start Stripe checkout.") from exc


def _paystack_checkout(user: User, payment: Payment, label: str, amount_cents: int, currency: str) -> str:
    settings = get_settings()
    if not settings.paystack_secret_key:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Paystack is not configured.")
    amount = amount_cents * 10 if currency.upper() == "NGN" else amount_cents
    # Paystack charges in the smallest currency unit. USD cents map 1:1; NGN display is kobo approximation.
    payload = {
        "email": user.email,
        "amount": amount,
        "currency": currency.upper(),
        "reference": str(payment.id),
        "callback_url": f"{settings.app_web_url}/app/billing?status=success",
        "metadata": {"payment_id": str(payment.id), "user_id": str(user.id), "label": label},
    }
    try:
        with httpx.Client(timeout=20) as client:
            response = client.post(
                "https://api.paystack.co/transaction/initialize",
                json=payload,
                headers={"Authorization": f"Bearer {settings.paystack_secret_key}"},
            )
        data = response.json()
        url = (data.get("data") or {}).get("authorization_url")
        if response.status_code >= 400 or not url:
            raise HTTPException(status.HTTP_502_BAD_GATEWAY, "Paystack did not return a checkout URL.")
        return url
    except HTTPException:
        raise
    except Exception as exc:
        log.error("paystack_checkout_failed", error=str(exc))
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, "Could not start Paystack checkout.") from exc


def _flutterwave_checkout(user: User, payment: Payment, label: str, amount_cents: int, currency: str) -> str:
    settings = get_settings()
    if not settings.flutterwave_secret_key:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Flutterwave is not configured.")
    payload = {
        "tx_ref": str(payment.id),
        "amount": round(amount_cents / 100, 2),
        "currency": currency.upper(),
        "redirect_url": f"{settings.app_web_url}/app/billing?status=success",
        "customer": {"email": user.email, "name": user.full_name or user.email},
        "customizations": {"title": "AcademicCheck AI", "description": label},
        "meta": {"payment_id": str(payment.id), "user_id": str(user.id)},
    }
    try:
        with httpx.Client(timeout=20) as client:
            response = client.post(
                "https://api.flutterwave.com/v3/payments",
                json=payload,
                headers={"Authorization": f"Bearer {settings.flutterwave_secret_key}"},
            )
        data = response.json()
        url = (data.get("data") or {}).get("link")
        if response.status_code >= 400 or not url:
            raise HTTPException(status.HTTP_502_BAD_GATEWAY, "Flutterwave did not return a checkout URL.")
        return url
    except HTTPException:
        raise
    except Exception as exc:
        log.error("flutterwave_checkout_failed", error=str(exc))
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, "Could not start Flutterwave checkout.") from exc


def _stripe_hmac(payload: bytes, signature: str, secret: str, tolerance: int) -> dict:
    parts = dict(item.split("=", 1) for item in signature.split(",") if "=" in item)
    timestamp = parts.get("t", "")
    try:
        age = abs(int(utcnow().timestamp()) - int(timestamp))
    except ValueError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid Stripe webhook timestamp.") from exc
    if age > tolerance:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Stripe webhook timestamp is too old.")
    expected = hmac.new(secret.encode(), f"{timestamp}.".encode() + payload, hashlib.sha256).hexdigest()
    if not constant_time_equals(expected, parts.get("v1", "")):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid Stripe webhook signature.")
    return json.loads(payload.decode())


# Legacy helper kept for existing imports in analysis paths.
def consume_credits(db: Session, user: User, operation: str, job_id: UUID | None = None) -> None:
    from app.services.credits import reserve_credits, consume_reservation

    if job_id is None:
        return
    reserve_credits(db, user, operation, job_id)
    consume_reservation(db, job_id)
