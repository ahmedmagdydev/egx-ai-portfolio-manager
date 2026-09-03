import json
import random
from datetime import UTC, datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path


def quantize(value: Decimal) -> str:
    return str(value.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP))


def generate_comi_bars(days: int = 252, seed: int = 42) -> list[dict]:
    rng = random.Random(seed)
    end = datetime(2025, 1, 15, tzinfo=UTC)
    close = Decimal("50.0000")
    bars: list[dict] = []
    current = end - timedelta(days=days * 2)
    while len(bars) < days:
        if current.weekday() < 5:
            change = Decimal(str(rng.uniform(-1.5, 1.5)))
            open_price = close + Decimal(str(rng.uniform(-0.3, 0.3)))
            new_close = open_price + change
            if new_close <= Decimal("0"):
                new_close = Decimal("0.0100")
            high = max(open_price, new_close) + Decimal(str(rng.uniform(0, 0.5)))
            low = min(open_price, new_close) - Decimal(str(rng.uniform(0, 0.5)))
            if low <= Decimal("0"):
                low = Decimal("0.0100")
            volume = rng.randint(80_000, 150_000)
            bars.append(
                {
                    "timestamp": current.replace(hour=10, minute=0, second=0)
                    .isoformat()
                    .replace("+00:00", "Z"),
                    "open": quantize(open_price),
                    "high": quantize(high),
                    "low": quantize(low),
                    "close": quantize(new_close),
                    "volume": volume,
                    "currency": "EGP",
                    "source": "mock",
                }
            )
            close = new_close
        current += timedelta(days=1)
    return bars[-days:]


def main() -> None:
    fixture_path = Path(__file__).with_name("mock_quotes.json")
    data = json.loads(fixture_path.read_text(encoding="utf-8"))
    data.setdefault("history", {})
    data["history"]["COMI"] = generate_comi_bars()
    fixture_path.write_text(json.dumps(data, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
