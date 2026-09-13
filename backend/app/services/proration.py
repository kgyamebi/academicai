"""Integer-cent proration. No floats. Ledger unit is always USD cents."""

from __future__ import annotations

from decimal import Decimal, ROUND_HALF_EVEN


def remaining_days(*, day_index: int, cycle_days: int) -> int:
    """day_index is 1-based (1 = first day of the period). Remaining unused days after today."""
    if cycle_days <= 0 or day_index < 1:
        raise ValueError("cycle_days and day_index must be positive")
    return max(0, cycle_days - day_index)


def _share_cents(amount_cents: int, remaining: int, cycle_days: int) -> int:
    if cycle_days <= 0:
        return 0
    share = (Decimal(amount_cents) * Decimal(remaining)) / Decimal(cycle_days)
    return int(share.quantize(Decimal("1"), rounding=ROUND_HALF_EVEN))


def prorate_plan_change(
    *,
    old_cents: int,
    new_cents: int,
    day_index: int,
    cycle_days: int = 30,
    policy: str = "upgrade_charge_downgrade_defer",
) -> dict:
    remaining = remaining_days(day_index=day_index, cycle_days=cycle_days)
    unused_old = _share_cents(old_cents, remaining, cycle_days)
    unused_new = _share_cents(new_cents, remaining, cycle_days)
    upgrade = new_cents > old_cents
    if policy != "upgrade_charge_downgrade_defer":
        raise ValueError("unsupported proration policy")
    if upgrade:
        charge = unused_new - unused_old
        return {
            "policy": policy,
            "upgrade": True,
            "deferred": False,
            "remaining_days": remaining,
            "unused_old_cents": unused_old,
            "unused_new_cents": unused_new,
            "charge_cents": max(0, charge),
            "credit_cents": 0,
        }
    return {
        "policy": policy,
        "upgrade": False,
        "deferred": True,
        "remaining_days": remaining,
        "unused_old_cents": unused_old,
        "unused_new_cents": unused_new,
        "charge_cents": 0,
        "credit_cents": 0,
    }


def apply_plan_change(subscription, new_plan, *, day_index: int, cycle_days: int = 30) -> dict:
    """Upgrade charges remaining difference now; downgrade is deferred to next cycle."""
    result = prorate_plan_change(
        old_cents=int(subscription.plan.price_usd_cents if subscription.plan else 0),
        new_cents=int(new_plan.price_usd_cents),
        day_index=day_index,
        cycle_days=cycle_days,
    )
    if result["upgrade"]:
        subscription.pending_plan_id = None
        return result
    subscription.pending_plan_id = new_plan.id
    return result
