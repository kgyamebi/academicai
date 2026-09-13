"""Currency minor-unit rounding. Display conversion never uses binary floats."""

from __future__ import annotations

from decimal import Decimal, ROUND_HALF_EVEN

# Whole-yen / whole-won / whole-dong: no fractional major units.
ZERO_DECIMAL = frozenset({"JPY", "KRW", "VND"})

# Display FX only. Ledger remains USD cents.
DISPLAY_RATES = {
    "USD": "1",
    "GHS": "15.4",
    "NGN": "1600",
    "KES": "129",
    "ZAR": "18.2",
    "GBP": "0.78",
    "EUR": "0.92",
    "INR": "84",
    "CAD": "1.37",
    "AUD": "1.52",
    "AED": "3.67",
    "BRL": "5.6",
    "MXN": "18.5",
    "PHP": "58",
    "IDR": "16200",
    "THB": "36",
    "VND": "25400",
    "PKR": "278",
    "BDT": "121",
    "JPY": "150",
    "KRW": "1380",
}


def localize_price(cents_usd: int, currency: str) -> dict:
    currency = (currency or "USD").upper()
    rate = Decimal(DISPLAY_RATES.get(currency, "1"))
    usd_major = Decimal(int(cents_usd)) / Decimal(100)
    major = usd_major * rate
    if currency in ZERO_DECIMAL:
        amount = major.quantize(Decimal("1"), rounding=ROUND_HALF_EVEN)
        minor = int(amount)
        places = 0
    else:
        amount = major.quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN)
        minor = int((amount * Decimal(100)).quantize(Decimal("1")))
        places = 2
    return {
        "currency": currency,
        "amount": int(amount) if places == 0 else float(amount),
        "amount_decimal": str(amount),
        "minor_units": minor,
        "usd_cents": int(cents_usd),
        "display_only": currency != "USD",
        "decimal_places": places,
    }


def charge_minor_units(cents_usd: int, currency: str) -> int:
    """Minor units to send to a PSP for a USD-cent catalog price. Ledger stays usd_cents."""
    localized = localize_price(cents_usd, currency)
    return int(localized["minor_units"])
