from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal

from .money import ZERO, quantize_money


class FinancialError(Exception):
    pass


@dataclass(frozen=True)
class FinancialSnapshot:
    symbol: str
    period_end: datetime
    period_type: str
    scope: str
    currency: str
    unit_scale: str
    price: Decimal | None
    price_as_of: datetime | None
    pe: Decimal | None
    pb: Decimal | None
    roe: Decimal | None
    roa: Decimal | None
    liabilities_to_equity: Decimal | None
    profit_margin: Decimal | None
    revenue_growth: Decimal | None
    earnings_growth: Decimal | None
    dividend_yield: Decimal | None
    warnings: list[str] = field(default_factory=list)


def scale_multiplier(scale: str) -> Decimal:
    if scale == "thousands":
        return Decimal("1000")
    if scale == "millions":
        return Decimal("1000000")
    return Decimal("1")


def price_to_earnings(price: Decimal, eps: Decimal | None) -> Decimal | None:
    if eps is None or eps <= ZERO:
        return None
    return quantize_money(price / eps)


def book_value_per_share(
    equity: Decimal | None,
    shares_outstanding: Decimal | None,
    scale: str = "units",
) -> Decimal | None:
    if equity is None or shares_outstanding is None or shares_outstanding == ZERO:
        return None
    actual_equity = equity * scale_multiplier(scale)
    return quantize_money(actual_equity / shares_outstanding)


def price_to_book(price: Decimal, bvps: Decimal | None) -> Decimal | None:
    if bvps is None or bvps == ZERO:
        return None
    return quantize_money(price / bvps)


def return_on_equity(
    net_income: Decimal | None,
    equity: Decimal | None,
    scale: str = "units",
) -> Decimal | None:
    if net_income is None or equity is None or equity == ZERO:
        return None
    actual_net_income = net_income * scale_multiplier(scale)
    actual_equity = equity * scale_multiplier(scale)
    return quantize_money(actual_net_income / actual_equity)


def return_on_assets(
    net_income: Decimal | None,
    assets: Decimal | None,
    scale: str = "units",
) -> Decimal | None:
    if net_income is None or assets is None or assets == ZERO:
        return None
    actual_net_income = net_income * scale_multiplier(scale)
    actual_assets = assets * scale_multiplier(scale)
    return quantize_money(actual_net_income / actual_assets)


def liabilities_to_equity(
    liabilities: Decimal | None,
    equity: Decimal | None,
    scale: str = "units",
) -> Decimal | None:
    if liabilities is None or equity is None or equity == ZERO:
        return None
    actual_liabilities = liabilities * scale_multiplier(scale)
    actual_equity = equity * scale_multiplier(scale)
    return quantize_money(actual_liabilities / actual_equity)


def profit_margin(
    net_income: Decimal | None,
    revenue: Decimal | None,
) -> Decimal | None:
    if net_income is None or revenue is None or revenue == ZERO:
        return None
    return quantize_money(net_income / revenue)


def growth(current: Decimal | None, prior: Decimal | None) -> Decimal | None:
    if current is None or prior is None or prior == ZERO:
        return None
    return quantize_money((current - prior) / prior)


def dividend_yield(
    dividends_per_share: Decimal | None,
    price: Decimal | None,
) -> Decimal | None:
    if dividends_per_share is None or price is None or price == ZERO:
        return None
    return quantize_money(dividends_per_share / price)
