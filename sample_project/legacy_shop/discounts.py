from __future__ import annotations

from datetime import date


def seasonal_discount(total: float, today: date | None = None) -> float:
    today = today or date.today()
    if today.month == 12 and total >= 1000:
        return total * 0.15
    if today.month in {7, 8} and total >= 500:
        return total * 0.08
    return 0.0


def loyalty_discount(total: float, previous_orders: int) -> float:
    if previous_orders > 20:
        return total * 0.12
    if previous_orders > 5:
        return total * 0.05
    return 0.0


def unused_promo_code_normalizer(code: str) -> str:
    return code.strip().replace("-", "").upper()

