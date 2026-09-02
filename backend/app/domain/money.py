from decimal import ROUND_HALF_EVEN, Decimal

ZERO = Decimal("0")
MONEY_QUANTUM = Decimal("0.01")
PRICE_QUANTUM = Decimal("0.0001")


def as_decimal(value: Decimal | int | str) -> Decimal:
    return value if isinstance(value, Decimal) else Decimal(str(value))


def quantize_money(value: Decimal) -> Decimal:
    return as_decimal(value).quantize(MONEY_QUANTUM, rounding=ROUND_HALF_EVEN)


def quantize_price(value: Decimal) -> Decimal:
    return as_decimal(value).quantize(PRICE_QUANTUM, rounding=ROUND_HALF_EVEN)
