import json
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

import pytest

from app.domain.money import quantize_money
from app.domain.portfolio import (
    HoldingState,
    InsufficientCashError,
    InsufficientHoldingsError,
    PriceQuote,
    TxnEvent,
    compute_allocation,
    compute_cash,
    compute_holdings,
    value_holdings,
)

FIXTURE = json.loads(
    (Path(__file__).parent / "fixtures" / "transactions_basic.json").read_text(encoding="utf-8")
)


def events_from_fixture() -> list[TxnEvent]:
    return [
        TxnEvent(
            type=item["type"],
            symbol=item.get("symbol"),
            quantity=Decimal(item["quantity"]) if item.get("quantity") else None,
            price=Decimal(item["price"]) if item.get("price") else None,
            fees=Decimal(item.get("fees", "0")),
            amount=Decimal(item["amount"]) if item.get("amount") else None,
            executed_at=datetime.fromisoformat(item["executed_at"]),
            sequence=index,
        )
        for index, item in enumerate(FIXTURE["transactions"], 1)
    ]


def test_golden_fixture() -> None:
    holdings = compute_holdings(events_from_fixture())
    cash = compute_cash(events_from_fixture())
    comi = holdings["COMI"]
    hrho = holdings["HRHO"]
    assert comi.avg_cost == Decimal("55.275")
    assert comi.quantity == Decimal("150")
    assert comi.total_cost == Decimal("8291.25")
    assert comi.realized_pnl == Decimal("866.25")
    assert hrho.quantity == Decimal("200")
    assert hrho.avg_cost == Decimal("20.05")
    assert cash == Decimal("87565")

    quote = PriceQuote(
        "COMI",
        Decimal("72.5"),
        "EGP",
        "mock",
        datetime(2025, 1, 15, tzinfo=UTC),
        "fresh",
    )
    valuations = value_holdings(holdings, {"COMI": quote, "HRHO": None})
    assert valuations[0].market_value == Decimal("10875.0")
    assert valuations[0].unrealized_pnl == Decimal("2583.75")
    assert valuations[1].market_value is None
    assert valuations[1].price_status == "unavailable"


def test_oversell_raises() -> None:
    events = events_from_fixture()
    events.append(
        TxnEvent(
            "SELL",
            "COMI",
            Decimal("151"),
            Decimal("70"),
            Decimal("0"),
            None,
            datetime.now(UTC),
            99,
        )
    )
    with pytest.raises(InsufficientHoldingsError) as error:
        compute_holdings(events)
    assert error.value.symbol == "COMI"
    assert error.value.held == Decimal("150")
    assert error.value.requested == Decimal("151")


def test_withdrawal_below_zero_raises() -> None:
    event = TxnEvent(
        "WITHDRAWAL",
        None,
        None,
        None,
        Decimal("0"),
        Decimal("1"),
        datetime.now(UTC),
        1,
    )
    with pytest.raises(InsufficientCashError):
        compute_cash([event])


def test_same_timestamp_sequence_controls_order() -> None:
    timestamp = datetime(2025, 1, 1, tzinfo=UTC)
    buy = TxnEvent("BUY", "COMI", Decimal("1"), Decimal("10"), Decimal("0"), None, timestamp, 2)
    sell = TxnEvent("SELL", "COMI", Decimal("1"), Decimal("10"), Decimal("0"), None, timestamp, 1)
    with pytest.raises(InsufficientHoldingsError):
        compute_holdings([buy, sell])


def test_zero_fee_and_full_liquidation() -> None:
    timestamp = datetime(2025, 1, 1, tzinfo=UTC)
    events = [
        TxnEvent("BUY", "COMI", Decimal("2"), Decimal("10"), Decimal("0"), None, timestamp, 1),
        TxnEvent("SELL", "COMI", Decimal("2"), Decimal("12"), Decimal("0"), None, timestamp, 2),
    ]
    state = compute_holdings(events)["COMI"]
    assert state.quantity == Decimal("0")
    assert state.avg_cost == Decimal("0")
    assert state.total_cost == Decimal("0")
    assert state.realized_pnl == Decimal("4")


def test_half_even_rounding_and_allocation_weights() -> None:
    assert quantize_money(Decimal("1.005")) == Decimal("1.00")
    assert quantize_money(Decimal("1.015")) == Decimal("1.02")
    quote = PriceQuote("COMI", Decimal("10"), "EGP", "mock", datetime.now(UTC), "fresh")
    holding = HoldingState("COMI", Decimal("10"), Decimal("50"), Decimal("5"), Decimal("0"))
    valuations = value_holdings({"COMI": holding}, {"COMI": quote}, {"COMI": "Banks"})
    report = compute_allocation(valuations, Decimal("50"))
    total_weight = (
        sum((line.weight for line in report.by_symbol), Decimal("0")) + report.cash.weight
    )
    assert total_weight == pytest.approx(1)
