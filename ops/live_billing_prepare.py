"""Prepare a live billing spot-check scenario. Does NOT charge a card.

Creates a pending Payment labeled as a harness test and (optionally) a provider
Checkout Session URL for the human to open and pay manually.

Requires:
  LIVE_BILLING_HARNESS=1
  LIVE_BILLING_USER_EMAIL=...
  LIVE_BILLING_PROVIDER=stripe|paystack|flutterwave
  DATABASE_URL / app settings as usual

Never calls confirm/capture/refund APIs.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import uuid
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

os.environ.setdefault("APP_ENV", os.environ.get("APP_ENV", "production"))

from sqlalchemy import create_engine, select  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app.config import get_settings  # noqa: E402
from app.models.billing import Credit, Payment  # noqa: E402
from app.models.user import User  # noqa: E402
from app.services.billing import _pending_payment, _provider_checkout  # noqa: E402


SESSIONS = ROOT / "ops" / "live_billing_sessions"


def _baseline_credits(db: Session, user_id) -> str:
    credit = db.scalar(select(Credit).where(Credit.user_id == user_id))
    if not credit:
        return "0"
    return str(credit.remaining)


def prepare_success_or_decline(*, scenario: str, email: str, provider: str, amount_cents: int, currency: str, create_checkout: bool) -> dict:
    settings = get_settings()
    engine = create_engine(settings.database_url, pool_pre_ping=True)
    stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    idem = f"live_harness:{scenario}:{email}:{stamp}:{uuid.uuid4().hex[:8]}"

    with Session(engine) as db:
        user = db.scalar(select(User).where(User.email == email.lower().strip()))
        if not user or user.is_guest:
            raise SystemExit(f"FAIL: no non-guest user for email={email}")
        baseline = _baseline_credits(db, user.id)
        # 1 credit for $1-ish spot check — ledger + clawback math stays simple.
        credits = Decimal("1")
        payment = _pending_payment(
            db,
            user,
            provider,
            amount_cents,
            currency,
            "credits",
            idem,
            {
                "credits": str(credits),
                "pack": "live_harness_micro",
                "live_harness": True,
                "scenario": scenario,
                "accounting_label": "LIVE_HARNESS_TEST — not product revenue",
            },
        )
        db.commit()
        db.refresh(payment)
        checkout_url = None
        if create_checkout:
            result = _provider_checkout(
                db,
                user,
                payment,
                f"LIVE_HARNESS_TEST {amount_cents}c ({scenario})",
                amount_cents,
                currency,
                recurring=False,
            )
            db.commit()
            checkout_url = (result or {}).get("checkout_url") or (result or {}).get("url")
            # _provider_checkout return shape
            if isinstance(result, dict):
                checkout_url = result.get("checkout_url") or result.get("authorization_url") or result.get("url") or checkout_url

        session = {
            "scenario": scenario,
            "stamp": stamp,
            "provider": provider,
            "payment_id": str(payment.id),
            "idempotency_key": payment.idempotency_key,
            "user_id": str(user.id),
            "email": email.lower().strip(),
            "amount_cents": amount_cents,
            "currency": currency.upper(),
            "credits_expected": str(credits),
            "baseline_credits_remaining": baseline,
            "checkout_url": checkout_url,
            "status_at_prepare": payment.status,
            "moves_money": False,
            "human_must_complete_payment": True,
            "label": "LIVE_HARNESS_TEST",
            "notes": (
                "Open checkout_url in a browser and complete or decline the charge yourself. "
                "This script does not click Pay and does not capture funds."
            ),
        }
    engine.dispose()
    return session


def prepare_refund(*, from_session_path: Path) -> dict:
    prior = json.loads(from_session_path.read_text(encoding="utf-8"))
    if prior.get("scenario") != "success":
        raise SystemExit("FAIL: refund prepare requires a success session file")
    stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    return {
        "scenario": "refund",
        "stamp": stamp,
        "provider": prior["provider"],
        "payment_id": prior["payment_id"],
        "idempotency_key": prior["idempotency_key"],
        "user_id": prior["user_id"],
        "email": prior["email"],
        "amount_cents": prior["amount_cents"],
        "currency": prior["currency"],
        "credits_expected": prior["credits_expected"],
        "baseline_credits_remaining": prior.get("post_success_credits_remaining")
        or prior["baseline_credits_remaining"],
        "refund_of_session": str(from_session_path),
        "checkout_url": None,
        "moves_money": False,
        "human_must_complete_refund": True,
        "label": "LIVE_HARNESS_TEST",
        "notes": (
            "In the provider Dashboard, fully refund this payment/charge. "
            "Do not use this script to call refund APIs. Then run verify."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare live billing spot-check (no charge)")
    parser.add_argument("--scenario", choices=("success", "decline", "refund"), required=True)
    parser.add_argument("--from-session", help="Required for refund: path to verified success session JSON")
    parser.add_argument("--force-refund-prepare", action="store_true", help="Skip verify_pass gate (not recommended)")
    parser.add_argument("--no-checkout", action="store_true", help="Only create pending Payment row; human uses other UI")
    args = parser.parse_args()

    if os.environ.get("LIVE_BILLING_HARNESS") != "1":
        print("FAIL: set LIVE_BILLING_HARNESS=1 to arm prepare", file=sys.stderr)
        return 2

    SESSIONS.mkdir(parents=True, exist_ok=True)
    amount = int(os.environ.get("LIVE_HARNESS_AMOUNT_CENTS", "100"))
    currency = (os.environ.get("LIVE_HARNESS_CURRENCY") or "USD").upper()
    provider = (os.environ.get("LIVE_BILLING_PROVIDER") or "stripe").lower()
    email = (os.environ.get("LIVE_BILLING_USER_EMAIL") or "").strip()

    if args.scenario == "refund":
        if not args.from_session:
            print("FAIL: --from-session required for refund", file=sys.stderr)
            return 2
        path = Path(args.from_session)
        prior = json.loads(path.read_text(encoding="utf-8"))
        if not prior.get("verify_pass") and not args.force_refund_prepare:
            print("FAIL: success session missing verify_pass=true", file=sys.stderr)
            return 1
        if args.force_refund_prepare:
            prior["verify_pass"] = True
            path.write_text(json.dumps(prior, indent=2), encoding="utf-8")
        session = prepare_refund(from_session_path=path)
    else:
        if not email:
            print("FAIL: set LIVE_BILLING_USER_EMAIL", file=sys.stderr)
            return 2
        session = prepare_success_or_decline(
            scenario=args.scenario,
            email=email,
            provider=provider,
            amount_cents=amount,
            currency=currency,
            create_checkout=not args.no_checkout,
        )

    out = SESSIONS / f"{session['scenario']}-{session['stamp']}.json"
    out.write_text(json.dumps(session, indent=2), encoding="utf-8")
    print(json.dumps({"wrote": str(out), "scenario": session["scenario"], "payment_id": session["payment_id"], "checkout_url": session.get("checkout_url"), "human_action_required": True}, indent=2))
    print("\n*** HUMAN ACTION REQUIRED: complete this payment/decline/refund yourself. Scripts will not. ***\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
