"""Reconcile internal payments against a provider sandbox/export snapshot.

Does not call live PSP APIs. Operators pass a JSON snapshot exported from the
sandbox dashboard (or a fixture). Intentionally mismatched rows are flagged.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.billing import Payment, PaymentTransaction


@dataclass
class ProviderTxn:
    provider: str
    provider_payment_id: str
    amount_cents: int
    currency: str
    status: str  # successful | failed | refunded | partially_refunded | pending


@dataclass
class Mismatch:
    kind: str
    payment_id: str | None
    provider_payment_id: str | None
    detail: str


def reconcile_against_provider_snapshot(db: Session, snapshot: list[ProviderTxn] | list[dict]) -> dict:
    """Compare DB payments to provider snapshot. Returns mismatches for audit."""
    rows: list[ProviderTxn] = []
    for item in snapshot:
        if isinstance(item, ProviderTxn):
            rows.append(item)
        else:
            rows.append(ProviderTxn(**item))

    by_provider_id = {r.provider_payment_id: r for r in rows if r.provider_payment_id}
    mismatches: list[Mismatch] = []

    payments = list(db.scalars(select(Payment)).all())
    internal_by_provider: dict[str, Payment] = {}
    for payment in payments:
        key = payment.provider_payment_id or ""
        if key:
            internal_by_provider[key] = payment

    for provider_id, remote in by_provider_id.items():
        local = internal_by_provider.get(provider_id)
        if local is None:
            # Also try matching pending payments by id string if provider uses our payment UUID as reference.
            try:
                local = db.get(Payment, UUID(provider_id))
            except (ValueError, TypeError):
                local = None
        if local is None:
            mismatches.append(
                Mismatch(
                    kind="missing_internal",
                    payment_id=None,
                    provider_payment_id=provider_id,
                    detail=f"Provider has {remote.status} {remote.amount_cents} {remote.currency}; internal missing",
                )
            )
            continue
        if local.amount_cents != remote.amount_cents:
            mismatches.append(
                Mismatch(
                    kind="amount_mismatch",
                    payment_id=str(local.id),
                    provider_payment_id=provider_id,
                    detail=f"internal={local.amount_cents} provider={remote.amount_cents}",
                )
            )
        if (local.currency or "").upper() != (remote.currency or "").upper():
            mismatches.append(
                Mismatch(
                    kind="currency_mismatch",
                    payment_id=str(local.id),
                    provider_payment_id=provider_id,
                    detail=f"internal={local.currency} provider={remote.currency}",
                )
            )
        if _normalize_status(local.status) != _normalize_status(remote.status):
            mismatches.append(
                Mismatch(
                    kind="status_mismatch",
                    payment_id=str(local.id),
                    provider_payment_id=provider_id,
                    detail=f"internal={local.status} provider={remote.status}",
                )
            )

    for payment in payments:
        if payment.status not in {"successful", "refunded", "partially_refunded"}:
            continue
        key = payment.provider_payment_id or str(payment.id)
        if key not in by_provider_id and str(payment.id) not in by_provider_id:
            mismatches.append(
                Mismatch(
                    kind="missing_provider",
                    payment_id=str(payment.id),
                    provider_payment_id=payment.provider_payment_id,
                    detail=f"Internal {payment.status} payment not in provider snapshot",
                )
            )

    # Ledger integrity: wallet-level checks are separate; here ensure success has a txn row.
    for payment in payments:
        if payment.status != "successful":
            continue
        txn = db.scalar(
            select(PaymentTransaction).where(
                PaymentTransaction.payment_id == payment.id,
                PaymentTransaction.event_type == "payment.successful",
            )
        )
        if txn is None:
            mismatches.append(
                Mismatch(
                    kind="missing_success_txn",
                    payment_id=str(payment.id),
                    provider_payment_id=payment.provider_payment_id,
                    detail="successful payment lacks payment.successful transaction",
                )
            )

    for payment in payments:
        unknown = db.scalar(
            select(PaymentTransaction).where(
                PaymentTransaction.payment_id == payment.id,
                PaymentTransaction.event_type == "charge.unknown",
            )
        )
        if unknown is not None:
            mismatches.append(
                Mismatch(
                    kind="charge_unknown",
                    payment_id=str(payment.id),
                    provider_payment_id=payment.provider_payment_id,
                    detail="processor timeout left charge unverified — do not assume success or failure",
                )
            )

    return {
        "checked_internal": len(payments),
        "checked_provider": len(rows),
        "mismatch_count": len(mismatches),
        "mismatches": [asdict(m) for m in mismatches],
        "ok": len(mismatches) == 0,
    }


def _normalize_status(status: str) -> str:
    s = (status or "").lower()
    if s in {"success", "succeeded", "paid", "successful"}:
        return "successful"
    if s in {"fail", "failed", "abandoned"}:
        return "failed"
    if s in {"refund", "refunded"}:
        return "refunded"
    if s in {"partial", "partially_refunded"}:
        return "partially_refunded"
    return s
