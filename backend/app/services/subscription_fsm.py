"""Subscription status transition guards — financial-grade allowed graph.

Statuses use the spelling already stored in the DB (`cancelled`).
Creating a new Subscription row is not a transition; use `assert_initial_status`.
"""

from __future__ import annotations

from fastapi import HTTPException, status

# Explicit financial states. `refunded` is modeled via payment ledger; subs cancel.
SUBSCRIPTION_STATUSES = frozenset(
    {"trialing", "active", "past_due", "suspended", "cancelled", "expired"}
)

# Allowed edges. Illegal transitions raise — no silent corruption.
ALLOWED_TRANSITIONS: dict[str, frozenset[str]] = {
    "trialing": frozenset({"active", "past_due", "cancelled", "expired", "suspended"}),
    "active": frozenset({"past_due", "cancelled", "expired", "suspended"}),
    "past_due": frozenset({"active", "cancelled", "suspended", "expired"}),
    "suspended": frozenset({"active", "cancelled", "expired"}),
    "cancelled": frozenset({"active"}),  # rare reopen; usual path is a new row
    "expired": frozenset({"active"}),
}


def assert_initial_status(new_status: str) -> str:
    status_name = (new_status or "").lower().strip()
    if status_name not in SUBSCRIPTION_STATUSES:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Unknown subscription status: {new_status}")
    return status_name


def assert_transition(current: str, new_status: str) -> str:
    cur = (current or "").lower().strip()
    nxt = assert_initial_status(new_status)
    if cur == nxt:
        return nxt
    if cur not in ALLOWED_TRANSITIONS:
        raise HTTPException(status.HTTP_409_CONFLICT, f"Subscription status {cur!r} is not transitionable.")
    if nxt not in ALLOWED_TRANSITIONS[cur]:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"Illegal subscription transition {cur} → {nxt}.",
        )
    return nxt


def apply_status(subscription, new_status: str) -> None:
    """Mutate subscription.status only if the edge is allowed."""
    nxt = assert_transition(subscription.status, new_status)
    subscription.status = nxt
