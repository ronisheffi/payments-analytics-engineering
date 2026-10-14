"""Decimal-safe money helpers. No BI allocation or FX conversion here."""

from __future__ import annotations

from decimal import Decimal, ROUND_HALF_EVEN

TWOPLACES = Decimal("0.01")
TAX_RATE = Decimal("0.10")
FOUR_PLACES = Decimal("0.0001")


def money(value: Decimal | int | str | float) -> Decimal:
    return Decimal(str(value)).quantize(TWOPLACES, rounding=ROUND_HALF_EVEN)


def tax_on(base: Decimal, rate: Decimal = TAX_RATE) -> Decimal:
    return money(base * rate)


def requested_amount(base: Decimal, tax: Decimal, tip: Decimal) -> Decimal:
    return money(base + tax + tip)


def rate(value: Decimal | str | float) -> Decimal:
    return Decimal(str(value)).quantize(FOUR_PLACES, rounding=ROUND_HALF_EVEN)
