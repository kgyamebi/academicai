from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.time import is_past
from app.models.billing import Credit, CreditTransaction
from app.models.user import User
from app.services.billing import OPERATION_CREDITS


def required_credits(operation: str) -> Decimal:
    return OPERATION_CREDITS.get(operation, Decimal("0"))


def available_credits(db: Session, user: User) -> Decimal:
    wallet = _wallet(db, user.id, lock=False)
    _expire_if_needed(db, wallet)
    return max(Decimal("0"), (wallet.remaining or Decimal("0")))


def reserve_credits(db: Session, user: User, operation: str, job_id: UUID) -> CreditTransaction | None:
    amount = required_credits(operation)
    if amount <= 0:
        return None
    wallet = _wallet(db, user.id, lock=True)
    _expire_if_needed(db, wallet)
    remaining = wallet.remaining or Decimal("0")
    if remaining < amount:
        raise HTTPException(
            status.HTTP_402_PAYMENT_REQUIRED,
            "You do not have enough credits for this analysis.",
        )
    existing = db.scalar(
        select(CreditTransaction).where(
            CreditTransaction.analysis_job_id == job_id,
            CreditTransaction.status == "reserved",
        )
    )
    if existing:
        return existing
    wallet.remaining = remaining - amount
    wallet.reserved = (wallet.reserved or Decimal("0")) + amount
    txn = CreditTransaction(
        user_id=user.id,
        credit_id=wallet.id,
        analysis_job_id=job_id,
        amount=amount,
        status="reserved",
        operation=operation,
    )
    db.add(txn)
    db.flush()
    return txn


def consume_reservation(db: Session, job_id: UUID) -> None:
    reserved = db.scalar(
        select(CreditTransaction).where(
            CreditTransaction.analysis_job_id == job_id,
            CreditTransaction.status == "reserved",
        )
    )
    if not reserved:
        return
    wallet = db.get(Credit, reserved.credit_id) if reserved.credit_id else None
    if wallet:
        wallet.reserved = max(Decimal("0"), (wallet.reserved or Decimal("0")) - reserved.amount)
    reserved.status = "consumed"


def refund_reservation(db: Session, job_id: UUID) -> None:
    reserved = db.scalar(
        select(CreditTransaction).where(
            CreditTransaction.analysis_job_id == job_id,
            CreditTransaction.status == "reserved",
        )
    )
    if not reserved:
        return
    wallet = db.get(Credit, reserved.credit_id) if reserved.credit_id else None
    if wallet:
        wallet.reserved = max(Decimal("0"), (wallet.reserved or Decimal("0")) - reserved.amount)
        wallet.remaining = (wallet.remaining or Decimal("0")) + reserved.amount
    reserved.status = "refunded"


def clawback_credits(db: Session, user: User, amount: Decimal, operation: str = "refund") -> Credit:
    wallet = _wallet(db, user.id, lock=True)
    current = wallet.remaining or Decimal("0")
    removed = min(current, max(Decimal("0"), amount))
    wallet.remaining = current - removed
    db.add(
        CreditTransaction(
            user_id=user.id,
            credit_id=wallet.id,
            amount=removed,
            status="refunded",
            operation=operation,
        )
    )
    return wallet


def grant_credits(db: Session, user: User, amount: Decimal, operation: str = "purchase") -> Credit:
    assert_wallet_integrity(db, user, stage="pre_grant")
    wallet = _wallet(db, user.id, lock=True)
    previous = wallet.remaining or Decimal("0")
    wallet.remaining = previous + amount
    db.add(
        CreditTransaction(
            user_id=user.id,
            credit_id=wallet.id,
            amount=amount,
            status="available",
            operation=operation,
            notes=f"previous={previous} new={wallet.remaining}",
        )
    )
    db.flush()
    assert_wallet_integrity(db, user, stage="post_grant")
    return wallet


def assert_wallet_integrity(db: Session, user: User, *, stage: str = "check") -> None:
    """Fail closed on ledger drift — no silent balance changes."""
    from app.core.logging import get_logger
    from app.core.metrics import incr

    if wallet_matches_ledger(db, user):
        return
    incr("billing.ledger_drift")
    get_logger("credits").error("ledger_drift_detected", user_id=str(user.id), stage=stage)
    raise HTTPException(
        status.HTTP_409_CONFLICT,
        "Credit ledger integrity check failed. Purchase blocked until reconciled.",
    )


def _wallet(db: Session, user_id: UUID, *, lock: bool) -> Credit:
    query = select(Credit).where(Credit.user_id == user_id)
    if lock:
        query = query.with_for_update()
    wallet = db.scalar(query)
    if wallet:
        return wallet
    wallet = Credit(user_id=user_id, remaining=Decimal("0"), reserved=Decimal("0"))
    db.add(wallet)
    db.flush()
    return wallet


def expected_remaining(db: Session, user_id: UUID) -> Decimal:
    """Rebuild remaining from credit_transactions. Reservation refunds restore remaining and are omitted."""
    rows = list(db.scalars(select(CreditTransaction).where(CreditTransaction.user_id == user_id)))
    available = sum((t.amount for t in rows if t.status == "available"), Decimal("0"))
    consumed = sum((t.amount for t in rows if t.status == "consumed"), Decimal("0"))
    reserved = sum((t.amount for t in rows if t.status == "reserved"), Decimal("0"))
    expired = sum((t.amount for t in rows if t.status == "expired"), Decimal("0"))
    clawback = sum(
        (t.amount for t in rows if t.status == "refunded" and t.analysis_job_id is None),
        Decimal("0"),
    )
    return available - consumed - reserved - expired - clawback


def wallet_matches_ledger(db: Session, user: User) -> bool:
    wallet = _wallet(db, user.id, lock=False)
    _expire_if_needed(db, wallet)
    remaining = wallet.remaining or Decimal("0")
    return remaining == expected_remaining(db, user.id)


def _expire_if_needed(db: Session, wallet: Credit) -> None:
    if wallet.expires_at and is_past(wallet.expires_at):
        remaining = wallet.remaining or Decimal("0")
        if remaining > 0:
            db.add(
                CreditTransaction(
                    user_id=wallet.user_id,
                    credit_id=wallet.id,
                    amount=remaining,
                    status="expired",
                    operation="expiry",
                )
            )
        wallet.remaining = Decimal("0")
        db.flush()
