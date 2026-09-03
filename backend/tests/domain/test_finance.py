from decimal import Decimal

from app.domain.finance import (
    book_value_per_share,
    dividend_yield,
    growth,
    liabilities_to_equity,
    price_to_book,
    price_to_earnings,
    profit_margin,
    return_on_assets,
    return_on_equity,
    scale_multiplier,
)


def test_scale_multiplier() -> None:
    assert scale_multiplier("units") == Decimal("1")
    assert scale_multiplier("thousands") == Decimal("1000")
    assert scale_multiplier("millions") == Decimal("1000000")


def test_price_to_earnings() -> None:
    assert price_to_earnings(Decimal("100"), Decimal("5")) == Decimal("20.00")


def test_price_to_earnings_rejects_zero_or_negative_eps() -> None:
    assert price_to_earnings(Decimal("100"), Decimal("0")) is None
    assert price_to_earnings(Decimal("100"), Decimal("-2")) is None
    assert price_to_earnings(Decimal("100"), None) is None


def test_book_value_per_share() -> None:
    bvps = book_value_per_share(Decimal("70000"), Decimal("1568000000"), scale="millions")
    assert bvps == Decimal("44.64")


def test_price_to_book() -> None:
    bvps = book_value_per_share(Decimal("70000"), Decimal("1568000000"), scale="millions")
    assert price_to_book(Decimal("72.5"), bvps) == Decimal("1.62")


def test_return_on_equity() -> None:
    roe = return_on_equity(Decimal("11500"), Decimal("85000"), scale="millions")
    assert roe == Decimal("0.14")


def test_return_on_assets() -> None:
    roa = return_on_assets(Decimal("11500"), Decimal("510000"), scale="millions")
    assert roa == Decimal("0.02")


def test_liabilities_to_equity() -> None:
    le = liabilities_to_equity(Decimal("425000"), Decimal("85000"), scale="millions")
    assert le == Decimal("5.00")


def test_profit_margin() -> None:
    margin = profit_margin(Decimal("11500"), Decimal("61000"))
    assert margin == Decimal("0.19")


def test_growth() -> None:
    g = growth(Decimal("61000"), Decimal("52000"))
    assert g == Decimal("0.17")


def test_dividend_yield() -> None:
    dy = dividend_yield(Decimal("0.50"), Decimal("72.5"))
    assert dy == Decimal("0.01")
