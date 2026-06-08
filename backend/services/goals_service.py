"""Financial goal FV calculations."""

from decimal import Decimal


def calculate_monthly_deposit(
    target: Decimal,
    current: Decimal,
    months: int,
    annual_return_pct: Decimal,
) -> Decimal:
    """Calculate required monthly deposit using future value formula."""
    if months <= 0:
        return Decimal("0")
    remaining = target - current
    if remaining <= 0:
        return Decimal("0")
    r = annual_return_pct / Decimal("100") / Decimal("12")
    if r == 0:
        return (remaining / months).quantize(Decimal("0.01"))
    factor = ((1 + r) ** months - 1) / r
    return (remaining / factor).quantize(Decimal("0.01"))


def goal_scenarios(
    target: Decimal,
    current: Decimal,
    months: int,
    annual_return_pct: Decimal,
    monthly_deposit: Decimal,
) -> dict:
    """Calculate what-if scenarios."""
    deposit_plus_10 = (monthly_deposit * Decimal("1.1")).quantize(Decimal("0.01"))
    months_plus_12 = months + 12
    deposit_extended = calculate_monthly_deposit(target, current, months_plus_12, annual_return_pct)
    return {
        "deposit_plus_10_pct": float(deposit_plus_10),
        "months_plus_12": months_plus_12,
        "deposit_with_extra_year": float(deposit_extended),
    }
