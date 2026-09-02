# Phase 01 demo

Start the local services with `make db-up`, `make migrate`, and `make backend`. Load the deterministic golden fixture through the API:

```bash
backend/.venv/bin/python backend/scripts/load_fixture.py backend/tests/domain/fixtures/transactions_basic.json
curl -s http://127.0.0.1:8000/portfolio/holdings
curl -s http://127.0.0.1:8000/portfolio/allocation
```

The fixture creates COMI and HRHO, then deposits EGP 100,000, buys both stocks, sells part of COMI, receives an EGP 150 dividend, and withdraws EGP 1,000. Expected values include COMI quantity `150`, average cost `55.2750`, total cost `8291.25`, realized P&L `866.25` (including the dividend), cash `87565.00`, and COMI market value `10875.00`. HRHO has an unavailable quote in the holdings response. Decimal values are returned as JSON strings.

Expected response shape:

```json
{"holdings":[{"symbol":"COMI","quantity":"150.0000","avg_cost":"55.2750","total_cost":"8291.25","market_value":"10875.00"}],"summary":{"cash":"87565.00","unpriced_count":1},"currency":"EGP"}
```

The mock provider is deterministic and is not live market data.
