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
    _expire_if_needed(wallet)
    return max(Decimal("0"), (wallet.remaining or Decimal("0")))


def reserve_credits(db: Session, user: User, operation: str, job_id: UUID) -> CreditTransaction | None:
    amount = required_credits(operation)
    if amount <= 0:
        return None
    wallet = _wallet(db, user.id, lock=True)
    _expire_if_needed(wallet)
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


def grant_credits(db: Session, user: User, amount: Decimal, operation: str = "purchase") -> Credit:
    wallet = _wallet(db, user.id, lock=True)
    wallet.remaining = (wallet.remaining or Decimal("0")) + amount
    db.add(
        CreditTransaction(
            user_id=user.id,
            credit_id=wallet.id,
            amount=amount,
            status="available",
            operation=operation,
        )
    )
    return wallet


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


def _expire_if_needed(wallet: Credit) -> None:
    if wallet.expires_at and is_past(wallet.expires_at):
        wallet.remaining = Decimal("0")
