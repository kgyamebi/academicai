"""Currency rounding — Decimal minor units, ledger stays USD cents."""

from __future__ import annotations

from decimal import Decimal

from app.db.session import SessionLocal
from app.models.billing import Payment
from app.models.user import User
from app.services.billing import apply_successful_payment, localize_price
from app.services.billing_money import ZERO_DECIMAL, charge_minor_units


def test_ghs_display_half_even_no_float_drift():
    # 299 USD cents * 15.4 = 46.046 → 46.05
    shown = localize_price(299, "GHS")
    expected = (Decimal("2.99") * Decimal("15.4")).quantize(Decimal("0.01"))
    assert shown["amount_decimal"] == str(expected)
    assert shown["minor_units"] == 4605
    assert shown["usd_cents"] == 299
    assert shown["display_only"] is True
    assert shown["decimal_places"] == 2


def test_jpy_zero_decimal_half_even():
    shown = localize_price(199, "JPY")
    expected = (Decimal("1.99") * Decimal("150")).quantize(Decimal("1"))
    assert shown["decimal_places"] == 0
    assert shown["amount_decimal"] == str(expected)
    assert shown["minor_units"] == int(expected)
    assert "." not in shown["amount_decimal"] or shown["amount_decimal"].endswith(".0") is False
    assert int(shown["amount"]) == int(expected)
    assert "JPY" in ZERO_DECIMAL


def test_krw_and_vnd_are_whole_units():
    krw = localize_price(199, "KRW")
    vnd = localize_price(199, "VND")
    assert krw["decimal_places"] == 0
    assert vnd["decimal_places"] == 0
    assert krw["minor_units"] == int((Decimal("1.99") * Decimal("1380")).quantize(Decimal("1")))
    assert vnd["minor_units"] == int((Decimal("1.99") * Decimal("25400")).quantize(Decimal("1")))


def test_usd_ledger_matches_display_and_charge():
    shown = localize_price(199, "USD")
    assert shown["usd_cents"] == 199
    assert shown["minor_units"] == 199
    assert shown["display_only"] is False
    assert charge_minor_units(199, "USD") == 199


def test_ledger_records_usd_cents_not_display_currency(client):
    db = SessionLocal()
    try:
        user = User(email="fx@example.com", password_hash="x", full_name="F", is_guest=False)
        db.add(user)
        db.flush()
        display = localize_price(299, "GHS")
        payment = Payment(
            user_id=user.id,
            provider="paystack",
            amount_cents=299,
            currency="USD",
            status="pending",
            purpose="credits",
            raw_payload={"credits": 10, "pack": "credits_10", "display": display},
        )
        db.add(payment)
        db.flush()
        apply_successful_payment(db, payment, "evt_fx", {"ok": True})
        db.commit()
        db.refresh(payment)
        assert payment.amount_cents == 299
        assert payment.currency == "USD"
        assert payment.raw_payload["display"]["minor_units"] == 4605
        assert payment.raw_payload["display"]["usd_cents"] == payment.amount_cents
    finally:
        db.close()
