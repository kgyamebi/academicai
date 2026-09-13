from __future__ import annotations

import hashlib
import hmac
import json
from datetime import timedelta
from decimal import Decimal
from threading import Lock
from uuid import UUID

import httpx
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.core.logging import get_logger
from app.core.security import constant_time_equals
from app.core.time import is_past, utcnow
from app.models.admin import WebhookEvent
from app.models.billing import Credit, CreditTransaction, Payment, PaymentTransaction, Plan, Subscription
from app.models.user import User
from app.services.ai.circuit import allow, record_failure, record_success
from app.services.emailer import send_email

log = get_logger("billing")

_apply_locks_guard = Lock()
_apply_locks: dict[str, Lock] = {}


def _payment_apply_lock(payment_id: UUID) -> Lock:
    with _apply_locks_guard:
        return _apply_locks.setdefault(str(payment_id), Lock())


def _record_billing_analytics(
    db: Session,
    event_name: str,
    *,
    user_id: UUID | None = None,
    properties: dict | None = None,
) -> None:
    """Persist privacy-safe billing funnel events (no document/assignment text)."""
    from app.models.admin import AnalyticsEvent

    safe = {k: v for k, v in (properties or {}).items() if k not in {"text", "document", "assignment", "content"}}
    db.add(
        AnalyticsEvent(
            user_id=user_id,
            event_name=event_name[:80],
            path="/api/billing",
            properties=str(safe)[:2000],
        )
    )


from app.services.billing_money import DISPLAY_RATES, localize_price  # noqa: F401

CREDIT_PACKS = [
    {"id": "credits_10", "credits": 10, "price_usd_cents": 299, "label": "10 credits"},
    {"id": "credits_50", "credits": 50, "price_usd_cents": 999, "label": "50 credits"},
]

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
    with _payment_apply_lock(payment.id):
        _apply_successful_payment_locked(db, payment, provider_event_id, payload)


def _apply_successful_payment_locked(db: Session, payment: Payment, provider_event_id: str, payload: dict) -> None:
    from sqlalchemy.exc import IntegrityError

    existing = db.scalar(select(PaymentTransaction).where(PaymentTransaction.provider_event_id == provider_event_id))
    if existing:
        return
    locked = db.scalar(select(Payment).where(Payment.id == payment.id).with_for_update())
    if locked is None:
        return
    payment = locked
    from app.core.metrics import incr

    if payment.status == "successful":
        try:
            with db.begin_nested():
                db.add(
                    PaymentTransaction(
                        payment_id=payment.id,
                        event_type="payment.acknowledged",
                        provider_event_id=provider_event_id,
                        status="successful",
                        payload=payload,
                    )
                )
                db.flush()
        except IntegrityError:
            return
        if payment.purpose == "subscription" and _is_subscription_renewal_event(payload):
            incr("billing.renewals")
            _extend_paid_period(db, payment)
        else:
            incr("billing.duplicate_success_events")
        return

    incr("billing.successful_payments")
    payment.status = "successful"
    payment.provider_payment_id = provider_event_id
    try:
        with db.begin_nested():
            db.add(
                PaymentTransaction(
                    payment_id=payment.id,
                    event_type="payment.successful",
                    provider_event_id=provider_event_id,
                    status="successful",
                    payload=payload,
                )
            )
            db.flush()
    except IntegrityError:
        return
    from app.services.billing_audit import append_audit

    user = db.get(User, payment.user_id)
    logical_id = _logical_purchase_id(payment)
    if logical_id and _already_entitled_logical_purchase(db, payment, logical_id):
        append_audit(
            db,
            event_type="payment.logical_duplicate",
            entity_type="payment",
            entity_id=str(payment.id),
            payload={"logical_purchase_id": logical_id, "provider": payment.provider},
        )
        return
    append_audit(
        db,
        event_type="payment.successful",
        entity_type="payment",
        entity_id=str(payment.id),
        payload={"purpose": payment.purpose, "amount_cents": payment.amount_cents, "provider": payment.provider},
    )
    if payment.purpose == "subscription" and user:
        plan_slug = (payment.raw_payload or {}).get("plan")
        plan = db.scalar(select(Plan).where(Plan.slug == plan_slug))
        if plan:
            past_due = db.scalar(
                select(Subscription)
                .where(
                    Subscription.user_id == user.id,
                    Subscription.plan_id == plan.id,
                    Subscription.status == "past_due",
                )
                .order_by(Subscription.created_at.desc())
            )
            if past_due:
                from app.services.dunning import recover_dunning

                recover_dunning(db, past_due)
                payment.subscription_id = past_due.id
                past_due.current_period_start = utcnow()
                past_due.current_period_end = utcnow() + timedelta(days=30)
                past_due.checks_used = 0
                send_email(user.email, "Subscription recovered", f"Your {plan.name} plan is active again.")
                _record_billing_analytics(
                    db,
                    "subscription_recovered",
                    user_id=user.id,
                    properties={"plan": plan.slug, "provider": payment.provider},
                )
            else:
                active = db.scalars(
                    select(Subscription).where(Subscription.user_id == user.id, Subscription.status == "active")
                ).all()
                for sub in active:
                    from app.services.subscription_fsm import apply_status

                    apply_status(sub, "cancelled")
                    sub.cancelled_at = utcnow()
                db.flush()
                from app.services.subscription_fsm import assert_initial_status

                db.add(
                    Subscription(
                        user_id=user.id,
                        plan_id=plan.id,
                        status=assert_initial_status("active"),
                        provider=payment.provider,
                        current_period_start=utcnow(),
                        current_period_end=utcnow() + timedelta(days=30),
                    )
                )
                db.flush()
                send_email(user.email, "Subscription confirmed", f"Your {plan.name} plan is now active.")
                _record_billing_analytics(
                    db,
                    "subscription_started",
                    user_id=user.id,
                    properties={"plan": plan.slug, "provider": payment.provider},
                )
    if payment.purpose == "credits" and user:
        from app.services.credits import grant_credits

        credits = Decimal(str((payment.raw_payload or {}).get("credits") or 0))
        if credits > 0:
            grant_credits(db, user, credits, "purchase")
            _record_billing_analytics(
                db,
                "credit_purchased",
                user_id=user.id,
                properties={"credits": str(credits), "provider": payment.provider},
            )


def mark_payment_failed(db: Session, payment: Payment, provider_event_id: str, payload: dict) -> None:
    existing = db.scalar(select(PaymentTransaction).where(PaymentTransaction.provider_event_id == provider_event_id))
    if existing:
        return
    if payment.status in {"successful", "refunded", "partially_refunded"}:
        return
    from app.core.metrics import incr

    incr("billing.failed_payments")
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
    from app.core.alerting import notify_payment_failure

    notify_payment_failure(
        provider=payment.provider,
        reason="payment marked failed",
        payment_id=str(payment.id),
        event_id=provider_event_id,
    )
    from app.services.billing_audit import append_audit

    append_audit(
        db,
        event_type="payment.failed",
        entity_type="payment",
        entity_id=str(payment.id),
        payload={"provider": payment.provider, "purpose": payment.purpose},
    )
    _record_billing_analytics(
        db,
        "payment_failed",
        user_id=payment.user_id,
        properties={"provider": payment.provider, "purpose": payment.purpose},
    )
    sub = _subscription_for_dunning(db, payment)
    if sub and sub.status in {"active", "past_due"}:
        from app.services.dunning import record_failed_renewal

        record_failed_renewal(db, sub)
        payment.subscription_id = sub.id


def mark_payment_cancelled(db: Session, payment: Payment, provider_event_id: str, payload: dict) -> None:
    existing = db.scalar(select(PaymentTransaction).where(PaymentTransaction.provider_event_id == provider_event_id))
    if existing:
        return
    if payment.status in {"successful", "refunded", "partially_refunded"}:
        return
    payment.status = "cancelled"
    db.add(
        PaymentTransaction(
            payment_id=payment.id,
            event_type="payment.cancelled",
            provider_event_id=provider_event_id,
            status="cancelled",
            payload=payload,
        )
    )


def apply_refund(
    db: Session,
    payment: Payment,
    provider_event_id: str,
    payload: dict,
    *,
    amount_cents: int | None = None,
) -> bool:
    """Apply a refund. Returns True if handled (applied or already recorded).

    Returns False when the payment is not yet successful so the webhook can be
    retried after a late success (out-of-order refund-before-charge).
    """
    existing = db.scalar(select(PaymentTransaction).where(PaymentTransaction.provider_event_id == provider_event_id))
    if existing:
        return True
    if payment.status in {"pending", "failed", "cancelled"}:
        return False
    if payment.status not in {"successful", "partially_refunded", "disputed"}:
        return True
    from app.core.metrics import incr

    full_amount = payment.amount_cents or 0
    already = _refunded_amount_cents(db, payment)
    remaining_refundable = max(0, full_amount - already)
    if remaining_refundable <= 0:
        db.add(
            PaymentTransaction(
                payment_id=payment.id,
                event_type="payment.refund_noop",
                provider_event_id=provider_event_id,
                status="refunded",
                payload=payload,
            )
        )
        return True
    requested = amount_cents if amount_cents is not None else remaining_refundable
    refunded = min(max(0, requested), remaining_refundable)
    if refunded <= 0:
        return True
    incr("billing.refunds")
    new_total = already + refunded
    partial = new_total < full_amount
    payment.status = "partially_refunded" if partial else "refunded"
    db.add(
        PaymentTransaction(
            payment_id=payment.id,
            event_type="payment.refunded",
            provider_event_id=provider_event_id,
            status=payment.status,
            payload={**(payload or {}), "amount_refunded_cents": refunded, "refund_total_cents": new_total},
        )
    )
    from app.services.billing_audit import append_audit

    append_audit(
        db,
        event_type="payment.refunded",
        entity_type="payment",
        entity_id=str(payment.id),
        payload={"refunded_cents": refunded, "partial": partial},
    )
    user = db.get(User, payment.user_id)
    if payment.purpose == "credits" and user:
        granted = Decimal(str((payment.raw_payload or {}).get("credits") or 0))
        if granted > 0 and full_amount > 0:
            clawback = granted * Decimal(refunded) / Decimal(full_amount)
            from app.services.credits import clawback_credits

            clawback_credits(db, user, clawback, "refund")
    if payment.purpose == "subscription" and user and not partial:
        active = db.scalars(
            select(Subscription).where(
                Subscription.user_id == user.id,
                Subscription.status.in_(("active", "suspended")),
                Subscription.provider == payment.provider,
            )
        ).all()
        for sub in active:
            from app.services.subscription_fsm import apply_status

            apply_status(sub, "cancelled")
            sub.cancelled_at = utcnow()
        db.flush()
        _record_billing_analytics(
            db,
            "subscription_cancelled",
            user_id=user.id,
            properties={"reason": "refund", "provider": payment.provider},
        )
    return True


def _refunded_amount_cents(db: Session, payment: Payment) -> int:
    rows = db.scalars(
        select(PaymentTransaction).where(
            PaymentTransaction.payment_id == payment.id,
            PaymentTransaction.event_type == "payment.refunded",
        )
    ).all()
    total = 0
    for row in rows:
        payload = row.payload or {}
        amount = payload.get("amount_refunded_cents")
        if amount is None:
            amount = payload.get("amount_refunded") or payload.get("amount")
        try:
            total += int(amount) if amount is not None else 0
        except (TypeError, ValueError):
            continue
    return total


def record_webhook_event(
    db: Session,
    provider: str,
    event_id: str,
    event_type: str,
    payload: bytes,
    *,
    mark_processed: bool = True,
) -> bool:
    """Return True if this event should be processed (new or previously unprocessed).

    Concurrent inserts race on the unique `event_id` constraint; IntegrityError
    means another worker won and this caller must not process.
    """
    from sqlalchemy.exc import IntegrityError

    existing = db.scalar(select(WebhookEvent).where(WebhookEvent.event_id == event_id))
    if existing:
        return existing.processed_at is None
    try:
        with db.begin_nested():
            db.add(
                WebhookEvent(
                    provider=provider,
                    event_id=event_id,
                    event_type=event_type,
                    payload_hash=hashlib.sha256(payload).hexdigest(),
                    processed_at=utcnow() if mark_processed else None,
                )
            )
            db.flush()
    except IntegrityError:
        existing = db.scalar(select(WebhookEvent).where(WebhookEvent.event_id == event_id))
        if existing:
            return existing.processed_at is None
        return False
    return True


def mark_webhook_processed(db: Session, event_id: str) -> None:
    event = db.scalar(select(WebhookEvent).where(WebhookEvent.event_id == event_id))
    if event and event.processed_at is None:
        event.processed_at = utcnow()
        db.flush()


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
        from app.core.metrics import incr

        incr("billing.webhook_signature_invalid")
        log.warning("stripe_webhook_signature_invalid", error=str(exc))
        from app.core.alerting import notify_payment_failure

        notify_payment_failure(provider="stripe", reason="invalid webhook signature")
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
        from app.core.metrics import incr

        incr("billing.webhook_signature_invalid")
        log.warning("paystack_webhook_signature_invalid")
        from app.core.alerting import notify_payment_failure

        notify_payment_failure(provider="paystack", reason="invalid webhook signature")
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid Paystack webhook signature.")
    event = json.loads(payload.decode())
    assert_webhook_event_freshness(event, provider="paystack")
    return event


def verify_flutterwave_signature(payload: bytes, signature: str | None) -> dict:
    settings = get_settings()
    secret = settings.flutterwave_webhook_hash
    if not secret:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Flutterwave webhooks are not configured.")
    if not signature or not constant_time_equals(secret, signature):
        from app.core.metrics import incr

        incr("billing.webhook_signature_invalid")
        log.warning("flutterwave_webhook_signature_invalid")
        from app.core.alerting import notify_payment_failure

        notify_payment_failure(provider="flutterwave", reason="invalid webhook signature")
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid Flutterwave webhook signature.")
    event = json.loads(payload.decode())
    assert_webhook_event_freshness(event, provider="flutterwave")
    return event


def assert_webhook_event_freshness(event: dict, *, provider: str) -> None:
    """Reject skewed events when a timestamp is present (Stripe already enforces via construct_event)."""
    from datetime import datetime
    from app.core.metrics import incr

    settings = get_settings()
    tol = int(settings.webhook_tolerance_seconds or 300)
    raw = _extract_webhook_timestamp(event)
    if raw is None:
        incr("billing.webhook_missing_timestamp")
        log.info("webhook_missing_timestamp", provider=provider)
        return
    try:
        if isinstance(raw, (int, float)):
            ts = float(raw)
            if ts > 1e12:
                ts = ts / 1000.0
        else:
            text = str(raw).replace("Z", "+00:00")
            ts = datetime.fromisoformat(text).timestamp()
    except Exception:  # noqa: BLE001
        incr("billing.webhook_bad_timestamp")
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid webhook timestamp.") from None
    age = abs(utcnow().timestamp() - ts)
    if age > tol:
        incr("billing.webhook_stale")
        log.warning("webhook_stale", provider=provider, age_s=int(age), tolerance_s=tol)
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Stale webhook event.")


def _extract_webhook_timestamp(event: dict) -> object | None:
    if not isinstance(event, dict):
        return None
    data = event.get("data") if isinstance(event.get("data"), dict) else {}
    for key in ("created_at", "paid_at", "createdAt", "event_time", "timestamp", "created"):
        if event.get(key) is not None:
            return event.get(key)
        if data.get(key) is not None:
            return data.get(key)
    return None


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
    if existing and existing.status in {"failed", "cancelled"}:
        existing.status = "pending"
        existing.amount_cents = amount_cents
        existing.currency = currency.upper()
        existing.purpose = purpose
        existing.raw_payload = _with_logical_id(raw_payload, idempotency_key)
        db.flush()
        return existing
    payment = Payment(
        user_id=user.id,
        provider=provider,
        amount_cents=amount_cents,
        currency=currency.upper(),
        status="pending",
        purpose=purpose,
        idempotency_key=idempotency_key,
        raw_payload=_with_logical_id(raw_payload, idempotency_key),
    )
    from sqlalchemy.exc import IntegrityError

    try:
        with db.begin_nested():
            db.add(payment)
            db.flush()
        return payment
    except IntegrityError:
        existing = db.scalar(select(Payment).where(Payment.idempotency_key == idempotency_key))
        if existing and existing.status == "pending":
            return existing
        if existing and existing.status == "successful":
            raise HTTPException(status.HTTP_409_CONFLICT, "This purchase was already completed.")
        if existing:
            return existing
        raise


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
        url = _stripe_checkout(db, user, payment, label, amount_cents, currency, recurring)
        return {"provider": "stripe", "payment_id": str(payment.id), "checkout_url": url, "mode": "stripe_checkout"}
    if provider == "paystack":
        url = _paystack_checkout(db, user, payment, label, amount_cents, currency)
        return {"provider": "paystack", "payment_id": str(payment.id), "checkout_url": url, "mode": "paystack_checkout"}
    if provider == "flutterwave":
        url = _flutterwave_checkout(db, user, payment, label, amount_cents, currency)
        return {
            "provider": "flutterwave",
            "payment_id": str(payment.id),
            "checkout_url": url,
            "mode": "flutterwave_checkout",
        }
    raise HTTPException(status.HTTP_400_BAD_REQUEST, "Unsupported payment provider.")


def _require_billing_circuit(provider: str) -> None:
    if not allow(provider):
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Payment provider is temporarily unavailable.")


def _is_processor_timeout(exc: BaseException) -> bool:
    name = type(exc).__name__.lower()
    text = str(exc).lower()
    return "timeout" in name or "timed out" in text or "timeout" in text


def _raise_provider_error(db: Session, payment: Payment, provider: str, exc: BaseException, fallback: str) -> None:
    record_failure(provider)
    if _is_processor_timeout(exc):
        record_ambiguous_charge(db, payment, reason=f"{provider} timeout")
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "Payment provider timed out. Charge is unverified and flagged for review.",
        ) from exc
    log.error(f"{provider}_checkout_failed", error=str(exc))
    raise HTTPException(status.HTTP_502_BAD_GATEWAY, fallback) from exc


def _stripe_checkout(
    db: Session, user: User, payment: Payment, label: str, amount_cents: int, currency: str, recurring: bool
) -> str:
    settings = get_settings()
    if not settings.stripe_secret_key:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Stripe is not configured.")
    _require_billing_circuit("stripe")
    try:
        import stripe

        stripe.api_key = settings.stripe_secret_key
        stripe.max_network_retries = 1
        stripe.default_http_client = stripe.new_default_http_client(timeout=15)
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
            record_failure("stripe")
            raise HTTPException(status.HTTP_502_BAD_GATEWAY, "Stripe did not return a checkout URL.")
        record_success("stripe")
        return session.url
    except HTTPException:
        raise
    except Exception as exc:
        _raise_provider_error(db, payment, "stripe", exc, "Could not start Stripe checkout.")


def _paystack_checkout(db: Session, user: User, payment: Payment, label: str, amount_cents: int, currency: str) -> str:
    settings = get_settings()
    if not settings.paystack_secret_key:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Paystack is not configured.")
    _require_billing_circuit("paystack")
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
        with httpx.Client(timeout=15) as client:
            response = client.post(
                "https://api.paystack.co/transaction/initialize",
                json=payload,
                headers={"Authorization": f"Bearer {settings.paystack_secret_key}"},
            )
        data = response.json()
        url = (data.get("data") or {}).get("authorization_url")
        if response.status_code >= 400 or not url:
            record_failure("paystack")
            raise HTTPException(status.HTTP_502_BAD_GATEWAY, "Paystack did not return a checkout URL.")
        record_success("paystack")
        return url
    except HTTPException:
        raise
    except Exception as exc:
        _raise_provider_error(db, payment, "paystack", exc, "Could not start Paystack checkout.")


def _flutterwave_checkout(db: Session, user: User, payment: Payment, label: str, amount_cents: int, currency: str) -> str:
    settings = get_settings()
    if not settings.flutterwave_secret_key:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Flutterwave is not configured.")
    _require_billing_circuit("flutterwave")
    payload = {
        "tx_ref": str(payment.id),
        "amount": float((Decimal(amount_cents) / Decimal("100")).quantize(Decimal("0.01"))),
        "currency": currency.upper(),
        "redirect_url": f"{settings.app_web_url}/app/billing?status=success",
        "customer": {"email": user.email, "name": user.full_name or user.email},
        "customizations": {"title": "AcademicCheck AI", "description": label},
        "meta": {"payment_id": str(payment.id), "user_id": str(user.id)},
    }
    try:
        with httpx.Client(timeout=15) as client:
            response = client.post(
                "https://api.flutterwave.com/v3/payments",
                json=payload,
                headers={"Authorization": f"Bearer {settings.flutterwave_secret_key}"},
            )
        data = response.json()
        url = (data.get("data") or {}).get("link")
        if response.status_code >= 400 or not url:
            record_failure("flutterwave")
            raise HTTPException(status.HTTP_502_BAD_GATEWAY, "Flutterwave did not return a checkout URL.")
        record_success("flutterwave")
        return url
    except HTTPException:
        raise
    except Exception as exc:
        _raise_provider_error(db, payment, "flutterwave", exc, "Could not start Flutterwave checkout.")


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
        from app.core.metrics import incr

        incr("billing.webhook_signature_invalid")
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid Stripe webhook signature.")
    return json.loads(payload.decode())


def _is_subscription_renewal_event(payload: dict | None) -> bool:
    event_type = str((payload or {}).get("type") or (payload or {}).get("event") or "")
    return event_type == "invoice.paid"


def _logical_purchase_id(payment: Payment) -> str:
    raw = payment.raw_payload if isinstance(payment.raw_payload, dict) else {}
    return str(raw.get("logical_purchase_id") or payment.idempotency_key or "")


def _with_logical_id(raw_payload: dict | None, idempotency_key: str) -> dict:
    raw = dict(raw_payload or {})
    raw.setdefault("logical_purchase_id", idempotency_key)
    return raw


def _already_entitled_logical_purchase(db: Session, payment: Payment, logical_id: str) -> bool:
    if not logical_id:
        return False
    others = db.scalars(
        select(Payment).where(
            Payment.id != payment.id,
            Payment.user_id == payment.user_id,
            Payment.status.in_(("successful", "refunded", "partially_refunded", "disputed")),
        )
    ).all()
    for other in others:
        if _logical_purchase_id(other) == logical_id:
            return True
    return False


def _subscription_for_dunning(db: Session, payment: Payment) -> Subscription | None:
    if payment.subscription_id:
        return db.get(Subscription, payment.subscription_id)
    if payment.purpose != "subscription":
        return None
    plan_slug = (payment.raw_payload or {}).get("plan")
    query = select(Subscription).where(
        Subscription.user_id == payment.user_id,
        Subscription.status.in_(("active", "past_due")),
        Subscription.provider == payment.provider,
    )
    if plan_slug:
        plan = db.scalar(select(Plan).where(Plan.slug == plan_slug))
        if plan is not None:
            query = query.where(Subscription.plan_id == plan.id)
    return db.scalar(query.order_by(Subscription.created_at.desc()))


def record_ambiguous_charge(db: Session, payment: Payment, *, reason: str) -> None:
    """Processor timeout/unreachable: never assume success or failure."""
    if payment.status != "pending":
        return
    event_id = f"charge.unknown:{payment.id}"
    existing = db.scalar(select(PaymentTransaction).where(PaymentTransaction.provider_event_id == event_id))
    if existing:
        return
    db.add(
        PaymentTransaction(
            payment_id=payment.id,
            event_type="charge.unknown",
            provider_event_id=event_id,
            status="unknown",
            payload={"reason": reason},
        )
    )
    from app.services.billing_audit import append_audit

    append_audit(
        db,
        event_type="charge.unknown",
        entity_type="payment",
        entity_id=str(payment.id),
        payload={"reason": reason, "provider": payment.provider},
    )
    from app.core.alerting import notify_payment_failure

    notify_payment_failure(
        provider=payment.provider,
        reason="ambiguous charge — needs review",
        payment_id=str(payment.id),
        event_id=event_id,
    )


def payment_from_dispute(db: Session, obj: dict | None) -> Payment | None:
    obj = obj or {}
    payment = payment_from_metadata(db, obj.get("metadata") if isinstance(obj.get("metadata"), dict) else {})
    if payment:
        return payment
    charge = obj.get("charge")
    if isinstance(charge, dict):
        payment = payment_from_metadata(db, charge.get("metadata") if isinstance(charge.get("metadata"), dict) else {})
        if payment:
            return payment
        charge = charge.get("id")
    if charge:
        found = db.scalar(select(Payment).where(Payment.provider_payment_id == str(charge)))
        if found:
            return found
    for key in ("payment_intent", "id", "flw_ref", "tx_ref"):
        value = obj.get(key)
        if not value:
            continue
        found = db.scalar(select(Payment).where(Payment.provider_payment_id == str(value)))
        if found:
            return found
        if key in {"id", "tx_ref"}:
            try:
                found = db.get(Payment, UUID(str(value)))
            except (ValueError, TypeError):
                found = None
            if found:
                return found
    return None


def _extend_paid_period(db: Session, payment: Payment) -> None:
    """Advance local period only when the current window is over or within 3 days of ending.

    Same-checkout Stripe `invoice.paid` after `checkout.session.completed` must not
    grant a second month or reset usage. Local cancel-at-period-end is not extended.
    """
    user = db.get(User, payment.user_id)
    if not user:
        return
    plan_slug = (payment.raw_payload or {}).get("plan")
    plan = db.scalar(select(Plan).where(Plan.slug == plan_slug)) if plan_slug else None
    query = select(Subscription).where(
        Subscription.user_id == user.id,
        Subscription.status.in_(("active", "past_due")),
        Subscription.cancel_at_period_end.is_(False),
    )
    if plan is not None:
        query = query.where(Subscription.plan_id == plan.id)
    sub = db.scalar(query.order_by(Subscription.created_at.desc()))
    if not sub:
        return
    if sub.current_period_end and not is_past(sub.current_period_end - timedelta(days=3)):
        return
    from app.services.subscription_fsm import apply_status

    apply_status(sub, "active")
    sub.dunning_attempts = 0
    sub.disputed_at = None
    sub.current_period_start = utcnow()
    sub.current_period_end = utcnow() + timedelta(days=30)
    sub.checks_used = 0


# Legacy helper kept for existing imports in analysis paths.
def consume_credits(db: Session, user: User, operation: str, job_id: UUID | None = None) -> None:
    from app.services.credits import reserve_credits, consume_reservation

    if job_id is None:
        return
    reserve_credits(db, user, operation, job_id)
    consume_reservation(db, job_id)
