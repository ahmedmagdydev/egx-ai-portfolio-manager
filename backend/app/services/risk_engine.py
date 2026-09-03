from __future__ import annotations

import math
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from typing import Any, TypedDict

from ..config import Settings
from ..domain.portfolio import (
    PriceQuote,
    compute_cash,
    compute_holdings,
    value_holdings,
)
from ..models import Stock
from ..schemas.risk import RebalancingSuggestion, RiskBreach, RiskLimits, RiskReport
from ..services.market_data import get_historical_prices, get_quote
from ..services.portfolio_service import current_events
from ..services.risk_limits import get_risk_limits


class Holding(TypedDict, total=False):
    symbol: str
    market_value: Decimal | None
    sector: str | None


def calculate_position_concentration(
    holdings: list[Holding], total_value: Decimal
) -> dict[str, Decimal]:
    if total_value == 0:
        return {}
    return {
        h["symbol"]: (h["market_value"] or Decimal("0")) / total_value
        for h in holdings
        if h.get("market_value")
    }


def calculate_sector_allocation(
    holdings: list[Holding], stocks: dict[str, Stock]
) -> dict[str, Decimal]:
    sectors: dict[str, Decimal] = {}
    total = Decimal("0")
    for h in holdings:
        value = h.get("market_value") or Decimal("0")
        sector = "Unknown"
        if h["symbol"] in stocks:
            sector = stocks[h["symbol"]].sector or "Unknown"
        sectors[sector] = sectors.get(sector, Decimal("0")) + value
        total += value
    if total == 0:
        return {k: Decimal("0") for k in sectors}
    return {k: v / total for k, v in sectors.items()}


def calculate_cash_percentage(cash: Decimal, total_value: Decimal) -> Decimal:
    if total_value == 0:
        return Decimal("0")
    return cash / total_value


def _price_series_for_symbol(
    session, settings: Settings, symbol: str, window_days: int
) -> list[tuple[date, Decimal]]:
    end = datetime.now(UTC)
    start = end - timedelta(days=window_days)
    bars = get_historical_prices(session, settings, symbol, start, end)
    series: list[tuple[date, Decimal]] = []
    for bar in bars:
        d = bar.timestamp.date() if isinstance(bar.timestamp, datetime) else bar.timestamp
        series.append((d, bar.close))
    return series


def _load_price_series(
    session, settings: Settings, symbols: list[str], window_days: int
) -> dict[str, list[tuple[date, Decimal]]]:
    return {
        symbol: _price_series_for_symbol(session, settings, symbol, window_days)
        for symbol in symbols
    }


def _portfolio_value_series(
    price_series: dict[str, list[tuple[date, Decimal]]],
    weights: dict[str, Decimal],
) -> list[tuple[date, Decimal]]:
    all_dates = sorted({d for series in price_series.values() for d, _ in series})
    price_lookup: dict[str, dict[date, Decimal]] = {
        symbol: {d: p for d, p in series} for symbol, series in price_series.items()
    }
    values: list[tuple[date, Decimal]] = []
    for d in all_dates:
        total = Decimal("0")
        for symbol, weight in weights.items():
            price = price_lookup.get(symbol, {}).get(d)
            if price is None:
                total = Decimal("0")
                break
            total += price * weight
        if total != 0:
            values.append((d, total))
    return values


def _returns(values: list[tuple[Any, Decimal]]) -> list[Decimal]:
    returns: list[Decimal] = []
    for i in range(1, len(values)):
        prev = values[i - 1][1]
        curr = values[i][1]
        if prev == 0:
            returns.append(Decimal("0"))
        else:
            returns.append((curr - prev) / prev)
    return returns


def _mean(values: list[Decimal]) -> Decimal:
    if not values:
        return Decimal("0")
    return sum(values, Decimal("0")) / Decimal(len(values))


def _std(values: list[Decimal]) -> Decimal:
    if len(values) < 2:
        return Decimal("0")
    m = _mean(values)
    variance = sum((v - m) ** 2 for v in values) / Decimal(len(values) - 1)
    return Decimal(math.sqrt(float(variance)))


def calculate_portfolio_volatility(
    price_series: dict[str, list[tuple[date, Decimal]]],
    weights: dict[str, Decimal],
    window_days: int = 90,
) -> Decimal | None:
    values = _portfolio_value_series(price_series, weights)
    if len(values) < 30:
        return None
    values = values[-window_days:]
    rets = _returns(values)
    if len(rets) < 2:
        return None
    daily_std = _std(rets)
    annualized = daily_std * Decimal(math.sqrt(252))
    return annualized.quantize(Decimal("0.0001"))


def calculate_max_drawdown(
    price_series: dict[str, list[tuple[date, Decimal]]],
    weights: dict[str, Decimal],
    window_days: int = 252,
) -> Decimal | None:
    values = _portfolio_value_series(price_series, weights)
    if len(values) < 30:
        return None
    values = values[-window_days:]
    peak = values[0][1]
    max_dd = Decimal("0")
    for _, v in values:
        if v > peak:
            peak = v
        dd = (peak - v) / peak if peak != 0 else Decimal("0")
        if dd > max_dd:
            max_dd = dd
    return (max_dd * 100).quantize(Decimal("0.0001"))


def _pair_returns(
    series_a: list[tuple[date, Decimal]], series_b: list[tuple[date, Decimal]]
) -> tuple[list[Decimal], list[Decimal]]:
    lookup_a = {d: p for d, p in series_a}
    lookup_b = {d: p for d, p in series_b}
    common = sorted(set(lookup_a) & set(lookup_b))
    rets_a: list[Decimal] = []
    rets_b: list[Decimal] = []
    for i in range(1, len(common)):
        pa_prev = lookup_a[common[i - 1]]
        pa_curr = lookup_a[common[i]]
        pb_prev = lookup_b[common[i - 1]]
        pb_curr = lookup_b[common[i]]
        rets_a.append((pa_curr - pa_prev) / pa_prev if pa_prev != 0 else Decimal("0"))
        rets_b.append((pb_curr - pb_prev) / pb_prev if pb_prev != 0 else Decimal("0"))
    return rets_a, rets_b


def calculate_correlation_matrix(
    price_series: dict[str, list[tuple[date, Decimal]]]
) -> dict[str, dict[str, Decimal | None]] | None:
    symbols = list(price_series.keys())
    if len(symbols) < 2:
        return None
    matrix: dict[str, dict[str, Decimal | None]] = {s: {} for s in symbols}
    for i, a in enumerate(symbols):
        matrix[a][a] = Decimal("1")
        for b in symbols[i + 1 :]:
            rets_a, rets_b = _pair_returns(price_series[a], price_series[b])
            if len(rets_a) < 30:
                corr: Decimal | None = None
            else:
                std_a = _std(rets_a)
                std_b = _std(rets_b)
                if std_a == 0 or std_b == 0:
                    corr = None
                else:
                    mean_a = _mean(rets_a)
                    mean_b = _mean(rets_b)
                    cov = sum(
                        (x - mean_a) * (y - mean_b)
                        for x, y in zip(rets_a, rets_b, strict=False)
                    ) / Decimal(len(rets_a) - 1)
                    corr = (cov / (std_a * std_b)).quantize(Decimal("0.0001"))
            matrix[a][b] = corr
            matrix[b][a] = corr
    return matrix


def calculate_beta(
    price_series: dict[str, list[tuple[date, Decimal]]],
    weights: dict[str, Decimal],
    benchmark_series: list[tuple[date, Decimal]] | None,
) -> Decimal | None:
    if benchmark_series is None or not benchmark_series:
        return None
    portfolio_values = _portfolio_value_series(price_series, weights)
    portfolio_returns = _returns(portfolio_values)
    benchmark_returns = _returns(benchmark_series)
    if len(portfolio_returns) < 30 or len(benchmark_returns) < 30:
        return None
    n = min(len(portfolio_returns), len(benchmark_returns))
    pr = portfolio_returns[-n:]
    br = benchmark_returns[-n:]
    std_b = _std(br)
    if std_b == 0:
        return None
    mean_p = _mean(pr)
    mean_b = _mean(br)
    cov = (
        sum((x - mean_p) * (y - mean_b) for x, y in zip(pr, br, strict=False))
        / Decimal(len(pr) - 1)
    )
    return (cov / std_b).quantize(Decimal("0.0001"))


def calculate_sharpe_ratio(
    price_series: dict[str, list[tuple[date, Decimal]]],
    weights: dict[str, Decimal],
    risk_free_rate_annual: Decimal,
) -> Decimal | None:
    values = _portfolio_value_series(price_series, weights)
    if len(values) < 30:
        return None
    rets = _returns(values)
    if len(rets) < 2:
        return None
    daily_rf = risk_free_rate_annual / Decimal("252")
    mean_return = _mean(rets)
    std = _std(rets)
    if std == 0:
        return None
    sharpe = ((mean_return - daily_rf) / std) * Decimal(math.sqrt(252))
    return sharpe.quantize(Decimal("0.0001"))


def _build_holdings_and_stocks(
    session, settings: Settings
) -> tuple[list[Holding], dict[str, Stock], Decimal, Decimal]:
    from sqlalchemy import select

    events = current_events(session)
    holdings_map = compute_holdings(events)
    cash = compute_cash(events)
    symbols = list(holdings_map.keys())
    stocks = {
        s.symbol: s
        for s in session.scalars(select(Stock).where(Stock.symbol.in_(symbols))).all()
    }
    raw_quotes = {symbol: get_quote(session, settings, symbol) for symbol in symbols}
    quotes: dict[str, PriceQuote | None] = {
        symbol: PriceQuote(
            symbol=q.symbol,
            price=q.price,
            currency=q.currency,
            source=q.source,
            observed_at=q.market_timestamp,
            freshness=q.freshness,
        )
        if q is not None
        else None
        for symbol, q in raw_quotes.items()
    }
    sectors = {symbol: stock.sector for symbol, stock in stocks.items()}
    valuations = value_holdings(holdings_map, quotes, sectors)
    holdings: list[Holding] = []
    total_value = cash
    for v in valuations:
        mv = v.market_value or Decimal("0")
        total_value += mv
        holdings.append(
            Holding(
                symbol=v.symbol,
                market_value=mv,
                sector=v.sector or "Unknown",
            )
        )
    return holdings, stocks, cash, total_value


def calculate_portfolio_risk(
    session, settings: Settings, *, window_days: int = 90
) -> RiskReport:
    limits_row = get_risk_limits(session)
    limits = RiskLimits.model_validate(limits_row)

    holdings, stocks, cash, total_value = _build_holdings_and_stocks(session, settings)
    if total_value < 0:
        raise ValueError("Total portfolio value must be non-negative")

    position_concentration = calculate_position_concentration(holdings, total_value)
    sector_exposure = calculate_sector_allocation(holdings, stocks)
    cash_percent = calculate_cash_percentage(cash, total_value)

    largest_position_symbol = ""
    largest_position_percent = Decimal("0")
    for symbol, weight in position_concentration.items():
        if weight > largest_position_percent:
            largest_position_symbol = symbol
            largest_position_percent = weight

    largest_sector = ""
    largest_sector_percent = Decimal("0")
    for sector, weight in sector_exposure.items():
        if weight > largest_sector_percent:
            largest_sector = sector
            largest_sector_percent = weight

    symbols = list(position_concentration.keys())
    weights = position_concentration
    price_series = _load_price_series(session, settings, symbols, window_days)

    volatility = calculate_portfolio_volatility(price_series, weights, window_days)
    drawdown = calculate_max_drawdown(price_series, weights, window_days=252)
    corr_matrix = calculate_correlation_matrix(price_series)
    beta = None
    sharpe = None
    missing: list[str] = []
    missing_ar: list[str] = []
    if len(symbols) == 0:
        missing.append("No holdings; volatility and drawdown unavailable.")
        missing_ar.append("لا توجد أصول؛ لا يمكن حساب التقلب والانخفاض.")
    elif any(len(s) < 30 for s in price_series.values()):
        missing.append("Insufficient price history for volatility/correlation metrics.")
        missing_ar.append("تاريخ الأسعار غير كافٍ لحساب مقاييس التقلب والارتباط.")
    else:
        missing.append("No benchmark series available; beta omitted.")
        missing_ar.append("لا توجد سلسلة مرجعية متاحة؛ تم حذف بيتا.")
        if (
            limits.max_drawdown_percent is not None
            and drawdown is not None
            and drawdown > limits.max_drawdown_percent
        ):
            pass
        sharpe = calculate_sharpe_ratio(price_series, weights, Decimal("0.10"))

    breaches = (
        _detect_breaches(
            limits,
            largest_position_symbol,
            largest_position_percent * 100,
            largest_sector,
            largest_sector_percent * 100,
            cash_percent * 100,
            volatility,
        )
        if total_value > 0
        else []
    )

    return RiskReport(
        total_portfolio_value=total_value,
        cash_percent=cash_percent * 100,
        largest_position_symbol=largest_position_symbol,
        largest_position_percent=largest_position_percent * 100,
        sector_exposure={k: v * 100 for k, v in sector_exposure.items()},
        largest_sector=largest_sector,
        largest_sector_percent=largest_sector_percent * 100,
        annualized_volatility=(volatility * 100 if volatility is not None else None),
        max_drawdown=drawdown,
        beta=beta,
        sharpe_ratio=sharpe,
        correlation_matrix=corr_matrix,
        breaches=breaches,
        missing_data=missing,
        missing_data_ar=missing_ar,
        data_as_of=datetime.now(UTC),
    )


def _detect_breaches(
    limits: RiskLimits,
    largest_position_symbol: str,
    largest_position_percent: Decimal,
    largest_sector: str,
    largest_sector_percent: Decimal,
    cash_percent: Decimal,
    volatility: Decimal | None,
) -> list[RiskBreach]:
    breaches: list[RiskBreach] = []
    if largest_position_percent > limits.max_single_position_percent:
        breaches.append(
            RiskBreach(
                rule="MAX_SINGLE_POSITION",
                severity="CRITICAL",
                current_value=largest_position_percent,
                limit_value=limits.max_single_position_percent,
                message_en=f"{largest_position_symbol} exceeds the single-position limit.",
                message_ar=f"{largest_position_symbol} يتجاوز حد المركز الفردي.",
                suggested_action_en="Consider reducing the position size.",
                suggested_action_ar="فكر في تقليل حجم المركز.",
            )
        )
    if largest_sector_percent > limits.max_sector_exposure_percent:
        breaches.append(
            RiskBreach(
                rule="MAX_SECTOR_EXPOSURE",
                severity="WARNING",
                current_value=largest_sector_percent,
                limit_value=limits.max_sector_exposure_percent,
                message_en=f"{largest_sector} sector exposure exceeds the limit.",
                message_ar=f"تعرض قطاع {largest_sector} يتجاوز الحد.",
                suggested_action_en="Diversify across sectors.",
                suggested_action_ar=" diversify الصناعة عبر القطاعات.",
            )
        )
    if cash_percent < limits.min_cash_percent:
        breaches.append(
            RiskBreach(
                rule="MIN_CASH",
                severity="CRITICAL",
                current_value=cash_percent,
                limit_value=limits.min_cash_percent,
                message_en="Cash position is below the minimum required.",
                message_ar="مركز النقدية أقل من الحد الأدنى المطلوب.",
                suggested_action_en="Increase cash reserves or reduce position sizes.",
                suggested_action_ar="زيادة الاحتياطي النقدي أو تقليل أحجام المراكز.",
            )
        )
    if (
        limits.max_portfolio_volatility_annual is not None
        and volatility is not None
        and volatility * 100 > limits.max_portfolio_volatility_annual
    ):
        breaches.append(
            RiskBreach(
                rule="MAX_PORTFOLIO_VOLATILITY",
                severity="WARNING",
                current_value=volatility * 100,
                limit_value=limits.max_portfolio_volatility_annual,
                message_en="Portfolio volatility exceeds the configured limit.",
                message_ar="تقلب المحفظة يتجاوز الحد المحدد.",
                suggested_action_en="Review high-volatility positions.",
                suggested_action_ar="مراجعة المراكز ذات التقلب العالي.",
            )
        )
    return breaches


def generate_rebalancing_suggestions(
    session, settings: Settings
) -> list[RebalancingSuggestion]:
    limits_row = get_risk_limits(session)
    limits = RiskLimits.model_validate(limits_row)
    holdings, stocks, cash, total_value = _build_holdings_and_stocks(session, settings)
    if total_value == 0:
        return []
    allocation = calculate_position_concentration(holdings, total_value)
    target = Decimal("1") / max(Decimal(len(allocation)), Decimal("1"))
    threshold = limits.rebalancing_threshold_percent / Decimal("100")
    suggestions: list[RebalancingSuggestion] = []
    for symbol, weight in allocation.items():
        diff = weight - target
        if abs(diff) < threshold:
            continue
        action = "REDUCE" if diff > 0 else "INCREASE"
        action_ar = "تقليل" if diff > 0 else "زيادة"
        suggestions.append(
            RebalancingSuggestion(
                symbol=symbol,
                action=action,
                action_ar=action_ar,
                current_percent=weight * 100,
                target_percent=target * 100,
                delta_shares_estimate=None,
                reason_en=f"Weight {weight:.2%} deviates from target {target:.2%}.",
                reason_ar=f"الوزن {weight:.2%} يختلف عن الهدف {target:.2%}.",
            )
        )
    return suggestions
