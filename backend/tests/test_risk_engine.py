from datetime import date, timedelta
from decimal import Decimal

from app.services.risk_engine import (
    calculate_cash_percentage,
    calculate_correlation_matrix,
    calculate_max_drawdown,
    calculate_portfolio_volatility,
    calculate_position_concentration,
    calculate_sector_allocation,
)


def holding(symbol: str, value: Decimal | None, sector: str = "Unknown") -> dict:
    return {"symbol": symbol, "market_value": value, "sector": sector}


def _series(prices: list[float]) -> list[tuple[date, Decimal]]:
    base = date(2025, 1, 1)
    return [
        (base + timedelta(days=i), Decimal(str(p)))
        for i, p in enumerate(prices)
    ]


def test_position_concentration() -> None:
    holdings = [holding("COMI", Decimal("7000")), holding("HRHO", Decimal("3000"))]
    weights = calculate_position_concentration(holdings, Decimal("10000"))
    assert weights == {"COMI": Decimal("0.7"), "HRHO": Decimal("0.3")}


def test_position_concentration_zero_total() -> None:
    assert calculate_position_concentration(
        [holding("COMI", Decimal("100"))], Decimal("0")
    ) == {}


def test_cash_percentage() -> None:
    assert calculate_cash_percentage(Decimal("1000"), Decimal("10000")) == Decimal("0.1")


def test_sector_allocation() -> None:
    from app.models import Stock

    stock_comi = Stock(symbol="COMI", name_en="COMI", currency="EGP", sector="Financials")
    stock_hrho = Stock(symbol="HRHO", name_en="HRHO", currency="EGP", sector="Real Estate")
    holdings = [
        holding("COMI", Decimal("6000"), "Financials"),
        holding("HRHO", Decimal("4000"), "Real Estate"),
    ]
    result = calculate_sector_allocation(holdings, {"COMI": stock_comi, "HRHO": stock_hrho})
    assert result == {
        "Financials": Decimal("0.6"),
        "Real Estate": Decimal("0.4"),
    }


def test_portfolio_volatility_with_flat_series() -> None:
    series_a = _series([100.0] * 40)
    weights = {"COMI": Decimal("1.0")}
    assert calculate_portfolio_volatility({"COMI": series_a}, weights) == Decimal("0")


def test_portfolio_volatility_insufficient_data() -> None:
    series = _series([100.0] * 10)
    assert calculate_portfolio_volatility({"COMI": series}, {"COMI": Decimal("1.0")}) is None


def test_max_drawdown() -> None:
    prices = [100.0] * 30 + [120.0, 110.0, 90.0, 95.0]
    series = _series(prices)
    dd = calculate_max_drawdown({"COMI": series}, {"COMI": Decimal("1.0")}, window_days=252)
    assert dd is not None
    assert dd > Decimal("0")


def test_correlation_matrix_insufficient_overlap() -> None:
    s1 = _series([100.0] * 35)
    s2 = _series([100.0] * 35)
    matrix = calculate_correlation_matrix({"COMI": s1, "HRHO": s2})
    assert matrix is not None
    assert matrix["COMI"]["HRHO"] is None


def test_correlation_matrix_perfect_positive() -> None:
    prices = [100.0 + i for i in range(40)]
    s1 = _series(prices)
    s2 = _series([p * 2 for p in prices])
    matrix = calculate_correlation_matrix({"COMI": s1, "HRHO": s2})
    assert matrix is not None
    assert matrix["COMI"]["HRHO"] is not None
    assert matrix["COMI"]["HRHO"] > Decimal("0.9999")
