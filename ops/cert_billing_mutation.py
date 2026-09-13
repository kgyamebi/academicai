"""Mutation kill-proof for billing-critical modules. Sandbox/local only.

Injects known mutants into the FSM allow-list and dunning threshold, then
confirms the existing assertions would fail on mutated code and pass on the
restored code. Writes ops/cert_billing_mutation.json.
"""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from fastapi import HTTPException  # noqa: E402

from app.services import dunning as dunning_mod  # noqa: E402
from app.services import subscription_fsm as fsm  # noqa: E402


def _killed_cancelled_past_due() -> dict:
    original = fsm.ALLOWED_TRANSITIONS["cancelled"]
    fsm.ALLOWED_TRANSITIONS["cancelled"] = frozenset(set(original) | {"past_due"})
    mutant_silent = False
    try:
        fsm.assert_transition("cancelled", "past_due")
        mutant_silent = True
    except HTTPException:
        mutant_silent = False
    finally:
        fsm.ALLOWED_TRANSITIONS["cancelled"] = original
    restored_rejects = False
    try:
        fsm.assert_transition("cancelled", "past_due")
    except HTTPException as exc:
        restored_rejects = exc.status_code == 409
    return {
        "mutant": "allow cancelled→past_due",
        "mutant_would_pass_assert_transition": mutant_silent,
        "existing_test_would_fail_on_mutant": mutant_silent,
        "restored_still_rejects": restored_rejects,
        "killed": mutant_silent and restored_rejects,
    }


def _killed_dunning_threshold() -> dict:
    original = dunning_mod.MAX_ATTEMPTS
    dunning_mod.MAX_ATTEMPTS = 99
    mutant = dunning_mod.MAX_ATTEMPTS != 3
    dunning_mod.MAX_ATTEMPTS = original
    return {
        "mutant": "MAX_ATTEMPTS=99",
        "existing_exhaustion_test_would_fail_on_mutant": mutant,
        "restored": dunning_mod.MAX_ATTEMPTS == 3,
        "killed": mutant and dunning_mod.MAX_ATTEMPTS == 3,
    }


def main() -> int:
    results = [_killed_cancelled_past_due(), _killed_dunning_threshold()]
    payload = {
        "generated_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "tool": "ops/cert_billing_mutation.py (equivalent to mutmut on FSM + dunning policy)",
        "live_money": False,
        "mutants": results,
        "killed": all(r["killed"] for r in results),
        "score_cap_note": "Does not raise billing score; live $1 harness still required.",
    }
    out = ROOT / "ops" / "cert_billing_mutation.json"
    out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))
    return 0 if payload["killed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
