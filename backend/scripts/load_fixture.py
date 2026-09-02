import json
import sys
from pathlib import Path

import httpx


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: load_fixture.py <path>", file=sys.stderr)
        return 2
    fixture = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    base_url = "http://127.0.0.1:8000"
    with httpx.Client(base_url=base_url, timeout=10) as client:
        for stock in fixture.get("stocks", []):
            response = client.post("/portfolio/stocks", json=stock)
            if response.status_code not in {201, 409}:
                response.raise_for_status()
            print(response.status_code, response.json())
        for transaction in fixture.get("transactions", []):
            response = client.post("/portfolio/transactions", json=transaction)
            response.raise_for_status()
            print(response.status_code, response.json())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
