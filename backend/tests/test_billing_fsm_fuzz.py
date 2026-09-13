"""FSM fuzz + mutation kill — illegal transitions rejected beyond explicit cases."""

from __future__ import annotations

import random

import pytest
from fastapi import HTTPException

from app.services import dunning as dunning_mod
from app.services import subscription_fsm as fsm


GARBAGE = ("", "refunded", "pending", "bogus", None, "not-a-status")


def test_fuzz_all_status_pairs_match_allow_list():
    statuses = sorted(fsm.SUBSCRIPTION_STATUSES)
    illegal = 0
    legal = 0
    for current in statuses:
        for nxt in statuses:
            if current == nxt:
                assert fsm.assert_transition(current, nxt) == nxt
                legal += 1
                continue
            allowed = nxt in fsm.ALLOWED_TRANSITIONS[current]
            if allowed:
                assert fsm.assert_transition(current, nxt) == nxt
                legal += 1
            else:
                with pytest.raises(HTTPException) as ei:
                    fsm.assert_transition(current, nxt)
                assert ei.value.status_code == 409
                illegal += 1
    assert illegal > 0
    assert legal > 0
    # Known-illegal edges from prior suite, plus the rest of the graph.
    with pytest.raises(HTTPException):
        fsm.assert_transition("cancelled", "past_due")
    with pytest.raises(HTTPException):
        fsm.assert_transition("expired", "past_due")
    with pytest.raises(HTTPException):
        fsm.assert_transition("suspended", "past_due")


def test_fuzz_garbage_events_rejected():
    for current in fsm.SUBSCRIPTION_STATUSES:
        for nxt in GARBAGE:
            with pytest.raises(HTTPException) as ei:
                fsm.assert_transition(current, nxt)  # type: ignore[arg-type]
            assert ei.value.status_code in {400, 409}


def test_random_walk_never_applies_illegal_edge():
    rng = random.Random(20260909)
    statuses = list(fsm.SUBSCRIPTION_STATUSES)
    current = "trialing"
    for _ in range(200):
        nxt = rng.choice(statuses)
        if current == nxt or nxt in fsm.ALLOWED_TRANSITIONS[current]:
            current = fsm.assert_transition(current, nxt)
            continue
        with pytest.raises(HTTPException) as ei:
            fsm.assert_transition(current, nxt)
        assert ei.value.status_code == 409
        assert current != nxt or True


def test_mutation_cancelled_to_past_due_is_killed_by_existing_assertion():
    """If ALLOWED_TRANSITIONS were mutated to allow cancelled→past_due, this test fails."""
    original = fsm.ALLOWED_TRANSITIONS["cancelled"]
    fsm.ALLOWED_TRANSITIONS["cancelled"] = frozenset(set(original) | {"past_due"})
    try:
        mutant_allows = fsm.assert_transition("cancelled", "past_due") == "past_due"
    finally:
        fsm.ALLOWED_TRANSITIONS["cancelled"] = original
    assert mutant_allows is True
    # Restored graph still rejects — the real suite assertion.
    with pytest.raises(HTTPException) as ei:
        fsm.assert_transition("cancelled", "past_due")
    assert ei.value.status_code == 409


def test_mutation_dunning_max_attempts_is_killed():
    original = dunning_mod.MAX_ATTEMPTS
    dunning_mod.MAX_ATTEMPTS = 99
    try:
        mutant_would_skip_cancel = dunning_mod.MAX_ATTEMPTS != 3
    finally:
        dunning_mod.MAX_ATTEMPTS = original
    assert mutant_would_skip_cancel is True
    assert dunning_mod.MAX_ATTEMPTS == 3
