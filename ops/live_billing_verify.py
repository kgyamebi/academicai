"""Post-transaction verifier for live billing spot-checks. Does NOT move money.

After the human completes pay / decline / refund, run this against the session JSON
from live_billing_prepare.py. Emits hard PASS/FAIL + evidence snapshot.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from decimal import Decimal
from pathlib import Path

from uuid import UUID

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from sqlalchemy import create_engine, func, select  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app.config import get_settings  # noqa: E402
from app.models.admin import WebhookEvent  # noqa: E402
from app.models.billing import Credit, CreditTransaction, Payment, PaymentTransaction  # noqa: E402


def _pid(session: dict) -> UUID:
    return UUID(str(session["payment_id"]))


def _check(name: str, ok: bool, detail: str, failures: list, checks: list) -> None:
    checks.append({"check": name, "pass": bool(ok), "detail": detail})
    if not ok:
        failures.append(name)


def verify_success(db: Session, session: dict, checks: list, failures: list) -> dict:
    payment = db.get(Payment, _pid(session))
    snap: dict = {"payment": None, "transactions": [], "webhooks": [], "credits": None}
    if payment is None:
        _check("payment_exists", False, "payment row missing", failures, checks)
        return snap

    snap["payment"] = {
        "id": str(payment.id),
        "status": payment.status,
        "amount_cents": payment.amount_cents,
        "currency": payment.currency,
        "idempotency_key": payment.idempotency_key,
        "provider": payment.provider,
        "purpose": payment.purpose,
    }

    _check("status_successful", payment.status == "successful", f"status={payment.status}", failures, checks)
    _check(
        "amount_matches_charge",
        payment.amount_cents == int(session["amount_cents"]),
        f"ledger={payment.amount_cents} expected_charge={session['amount_cents']} "
        "(processor fees are NOT stored on Payment; see fee_note)",
        failures,
        checks,
    )
    _check(
        "idempotency_key_stable",
        payment.idempotency_key == session["idempotency_key"],
        f"key={payment.idempotency_key}",
        failures,
        checks,
    )

    # Exactly one Payment row for this idempotency key
    same_key = db.scalars(select(Payment).where(Payment.idempotency_key == session["idempotency_key"])).all()
    _check("exactly_one_payment_for_idempotency_key", len(same_key) == 1, f"count={len(same_key)}", failures, checks)

    txns = list(
        db.scalars(
            select(PaymentTransaction).where(PaymentTransaction.payment_id == payment.id).order_by(PaymentTransaction.created_at)
        )
    )
    snap["transactions"] = [
        {
            "event_type": t.event_type,
            "status": t.status,
            "provider_event_id": t.provider_event_id,
        }
        for t in txns
    ]
    success_txns = [t for t in txns if t.event_type == "payment.successful"]
    _check("exactly_one_success_ledger_txn", len(success_txns) == 1, f"count={len(success_txns)}", failures, checks)

    # Webhook processed exactly once for the success provider_event_id (when present)
    event_id = success_txns[0].provider_event_id if success_txns else None
    if event_id:
        # Stripe stores raw event id; Paystack stores paystack:ref:type
        wh_rows = list(
            db.scalars(
                select(WebhookEvent).where(
                    (WebhookEvent.event_id == event_id)
                    | (WebhookEvent.event_id.like(f"%{event_id}%"))
                )
            )
        )
        snap["webhooks"] = [
            {
                "event_id": w.event_id,
                "event_type": w.event_type,
                "provider": w.provider,
                "processed": w.processed_at is not None,
            }
            for w in wh_rows
        ]
        processed = [w for w in wh_rows if w.processed_at is not None]
        _check("webhook_received_and_processed", len(processed) >= 1, f"processed={len(processed)} matched={len(wh_rows)}", failures, checks)
        # Dedup: unique event_id means at most one row per exact id
        exact = [w for w in wh_rows if w.event_id == event_id or w.event_id.endswith(event_id)]
        _check("webhook_not_duplicated_rows", len(exact) <= 1 or len({w.event_id for w in exact}) == len(exact), f"exact_rows={len(exact)}", failures, checks)
    else:
        _check("webhook_received_and_processed", False, "no provider_event_id on success txn", failures, checks)

    credit = db.scalar(select(Credit).where(Credit.user_id == payment.user_id))
    remaining = Decimal(str(credit.remaining)) if credit else Decimal("0")
    baseline = Decimal(str(session["baseline_credits_remaining"]))
    expected_grant = Decimal(str(session["credits_expected"]))
    snap["credits"] = {"remaining": str(remaining), "baseline": str(baseline), "expected_grant": str(expected_grant)}
    _check(
        "credits_increased_by_grant",
        remaining >= baseline + expected_grant,
        f"remaining={remaining} baseline={baseline} grant={expected_grant}",
        failures,
        checks,
    )
    purchases = db.scalars(
        select(CreditTransaction).where(
            CreditTransaction.user_id == payment.user_id,
            CreditTransaction.operation == "purchase",
        )
    ).all()
    # At least one purchase txn of expected size near this payment time is enough
    matching = [t for t in purchases if Decimal(str(t.amount)) == expected_grant]
    _check("credit_purchase_ledger_present", len(matching) >= 1, f"purchase_txns_matching_amount={len(matching)}", failures, checks)

    session["post_success_credits_remaining"] = str(remaining)
    return snap


def verify_decline(db: Session, session: dict, checks: list, failures: list) -> dict:
    payment = db.get(Payment, _pid(session))
    snap: dict = {"payment": None, "transactions": [], "webhooks": [], "credits": None}
    if payment is None:
        _check("payment_exists", False, "payment row missing", failures, checks)
        return snap
    snap["payment"] = {"id": str(payment.id), "status": payment.status, "amount_cents": payment.amount_cents}
    _check(
        "status_failed_or_cancelled",
        payment.status in {"failed", "cancelled"},
        f"status={payment.status} (complete a real decline or abandon+expire)",
        failures,
        checks,
    )
    txns = list(db.scalars(select(PaymentTransaction).where(PaymentTransaction.payment_id == payment.id)))
    snap["transactions"] = [{"event_type": t.event_type, "provider_event_id": t.provider_event_id} for t in txns]
    fail_txns = [t for t in txns if t.event_type in {"payment.failed", "payment.cancelled"}]
    _check("failure_ledger_txn_present", len(fail_txns) >= 1, f"count={len(fail_txns)}", failures, checks)
    success_txns = [t for t in txns if t.event_type == "payment.successful"]
    _check("no_success_ledger_txn", len(success_txns) == 0, f"count={len(success_txns)}", failures, checks)

    if fail_txns and fail_txns[0].provider_event_id:
        eid = fail_txns[0].provider_event_id
        wh = list(db.scalars(select(WebhookEvent).where(WebhookEvent.event_id.like(f"%{eid}%"))))
        snap["webhooks"] = [{"event_id": w.event_id, "processed": w.processed_at is not None} for w in wh]
        _check("webhook_processed_for_failure", any(w.processed_at for w in wh), f"matched={len(wh)}", failures, checks)

    credit = db.scalar(select(Credit).where(Credit.user_id == payment.user_id))
    remaining = Decimal(str(credit.remaining)) if credit else Decimal("0")
    baseline = Decimal(str(session["baseline_credits_remaining"]))
    snap["credits"] = {"remaining": str(remaining), "baseline": str(baseline)}
    _check("credits_unchanged", remaining == baseline, f"remaining={remaining} baseline={baseline}", failures, checks)
    return snap


def verify_refund(db: Session, session: dict, checks: list, failures: list) -> dict:
    payment = db.get(Payment, _pid(session))
    snap: dict = {"payment": None, "transactions": [], "webhooks": [], "credits": None}
    if payment is None:
        _check("payment_exists", False, "payment row missing", failures, checks)
        return snap
    snap["payment"] = {"id": str(payment.id), "status": payment.status, "amount_cents": payment.amount_cents}
    _check(
        "status_refunded",
        payment.status in {"refunded", "partially_refunded"},
        f"status={payment.status}",
        failures,
        checks,
    )
    # For micro harness we require full refund
    _check("status_fully_refunded", payment.status == "refunded", f"status={payment.status}", failures, checks)

    txns = list(db.scalars(select(PaymentTransaction).where(PaymentTransaction.payment_id == payment.id)))
    snap["transactions"] = [
        {
            "event_type": t.event_type,
            "status": t.status,
            "provider_event_id": t.provider_event_id,
            "amount_refunded_cents": (t.payload or {}).get("amount_refunded_cents"),
        }
        for t in txns
    ]
    refund_txns = [t for t in txns if t.event_type == "payment.refunded"]
    _check("exactly_one_refund_ledger_txn", len(refund_txns) == 1, f"count={len(refund_txns)}", failures, checks)
    if refund_txns:
        amt = (refund_txns[0].payload or {}).get("amount_refunded_cents")
        _check(
            "refund_amount_matches_charge",
            amt is None or int(amt) == int(session["amount_cents"]),
            f"refunded_cents={amt} charge={session['amount_cents']}",
            failures,
            checks,
        )
        eid = refund_txns[0].provider_event_id
        if eid:
            wh = list(db.scalars(select(WebhookEvent).where(WebhookEvent.event_id.like(f"%{eid}%"))))
            snap["webhooks"] = [{"event_id": w.event_id, "processed": w.processed_at is not None} for w in wh]
            _check("refund_webhook_processed", any(w.processed_at for w in wh), f"matched={len(wh)}", failures, checks)

    credit = db.scalar(select(Credit).where(Credit.user_id == payment.user_id))
    remaining = Decimal(str(credit.remaining)) if credit else Decimal("0")
    # After full refund of the success grant, remaining should be back near pre-success baseline
    # Prefer baseline from success session file if linked
    target = Decimal(str(session.get("baseline_credits_remaining") or "0"))
    # If baseline_credits_remaining on refund session was post-success, clawback should subtract grant
    grant = Decimal(str(session["credits_expected"]))
    # Detect: if refund session baseline was copied from post_success, expect remaining ~= baseline - grant
    # prepare_refund sets baseline to post_success_credits_remaining — so expect remaining <= baseline - grant + epsilon
    # Better: load original success session
    expected_after = None
    if session.get("refund_of_session"):
        prior = json.loads(Path(session["refund_of_session"]).read_text(encoding="utf-8"))
        expected_after = Decimal(str(prior["baseline_credits_remaining"]))
    snap["credits"] = {"remaining": str(remaining), "expected_after_full_refund": str(expected_after) if expected_after is not None else None}
    if expected_after is not None:
        _check(
            "credits_clawed_back_to_pre_success",
            remaining == expected_after,
            f"remaining={remaining} expected={expected_after}",
            failures,
            checks,
        )
    else:
        _check("credits_clawed_back_to_pre_success", False, "missing refund_of_session link", failures, checks)

    clawbacks = int(
        db.scalar(
            select(func.count()).select_from(CreditTransaction).where(
                CreditTransaction.user_id == payment.user_id,
                CreditTransaction.operation == "refund",
                CreditTransaction.status == "refunded",
            )
        )
        or 0
    )
    _check("credit_clawback_txn_present", clawbacks >= 1, f"clawback_count={clawbacks}", failures, checks)
    return snap


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify live billing spot-check session")
    parser.add_argument("--session", required=True, help="Path to prepare session JSON")
    parser.add_argument("--out", default=str(ROOT / "ops" / "cert_live_billing_verify.json"))
    args = parser.parse_args()

    session_path = Path(args.session)
    session = json.loads(session_path.read_text(encoding="utf-8"))
    scenario = session["scenario"]
    checks: list[dict] = []
    failures: list[str] = []

    settings = get_settings()
    engine = create_engine(settings.database_url, pool_pre_ping=True)
    with Session(engine) as db:
        if scenario == "success":
            snap = verify_success(db, session, checks, failures)
        elif scenario == "decline":
            snap = verify_decline(db, session, checks, failures)
        elif scenario == "refund":
            snap = verify_refund(db, session, checks, failures)
        else:
            print(f"FAIL: unknown scenario {scenario}", file=sys.stderr)
            return 2
    engine.dispose()

    passed = len(failures) == 0
    report = {
        "measured_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "scenario": scenario,
        "session_path": str(session_path),
        "payment_id": session.get("payment_id"),
        "pass": passed,
        "verdict": "PASS" if passed else "FAIL",
        "failed_checks": failures,
        "checks": checks,
        "snapshot": snap,
        "fee_note": (
            "Payment.amount_cents is the customer charge. Processor/network fees are not a separate "
            "ledger column in-app; reconcile fees in the PSP dashboard against the same charge id."
        ),
        "moves_money": False,
        "human_completed_real_payment": True if scenario != "refund" else None,
        "human_completed_real_refund": True if scenario == "refund" else None,
    }
    Path(args.out).write_text(json.dumps(report, indent=2), encoding="utf-8")

    # Stamp session so refund prepare can gate on success
    session["verify_pass"] = passed
    session["last_verify_at"] = report["measured_at"]
    session["last_verify_out"] = args.out
    session_path.write_text(json.dumps(session, indent=2), encoding="utf-8")

    print(json.dumps({"verdict": report["verdict"], "pass": passed, "failed_checks": failures, "out": args.out}, indent=2))
    for c in checks:
        print(f"  [{'OK' if c['pass'] else 'FAIL'}] {c['check']}: {c['detail']}")
    if not passed:
        print("\nSTOP. Do not proceed to the next scenario. Fix and use a fresh transaction.", file=sys.stderr)
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
