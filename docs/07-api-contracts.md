# 07 — API Contracts

## Purpose

This document defines the FastAPI contract conventions, versioning strategy, response and error envelopes, pagination, freshness metadata, and endpoint-level contracts for the local single-user EGX portfolio assistant. It does not create routes or code; it specifies the contract future routes must implement.

## API conventions

1. Base path: `/api/v1`.
2. JSON request/response bodies. `Content-Type` is `application/json` unless otherwise stated.
3. All response payloads are objects; list endpoints return an object containing an `items` array and pagination fields.
4. HTTP status codes are used consistently:
   - `200 OK` for successful reads and updates.
   - `201 Created` for successful creation.
   - `204 No Content` only where explicitly documented.
   - `400 Bad Request` for validation errors.
   - `401 Unauthorized` reserved for future authentication.
   - `403 Forbidden` reserved for future authorization.
   - `404 Not Found` for missing resources.
   - `422 Unprocessable Entity` for semantic business-rule violations (oversell, insufficient cash, stale data requested as fresh).
   - `429 Too Many Requests` for rate limiting.
   - `503 Service Unavailable` for upstream failures such as Ollama or market provider unavailability.
   - `500 Internal Server Error` for unexpected failures.
5. Every response includes a top-level `meta` object with `request_id`, `timestamp`, and `api_version`.
6. Error responses include `error.code`, `error.message`, and optionally `error.details`. The message is safe for the UI; details are only useful when they do not leak secrets, paths, or portfolio data.

## Response envelope

```json
{
  "data": { ... },
  "meta": {
    "request_id": "uuid",
    "timestamp": "2026-09-02T12:00:00Z",
    "api_version": "v1"
  }
}
```

For list endpoints:

```json
{
  "data": {
    "items": [ ... ],
    "pagination": {
      "page": 1,
      "page_size": 20,
      "total": 100
    }
  },
  "meta": { ... }
}
```

For errors:

```json
{
  "error": {
    "code": "SYMBOL_NOT_FOUND",
    "message": "The requested symbol was not found in the local stock universe."
  },
  "meta": { ... }
}
```

## Freshness metadata

Any response containing market or financial data includes a `freshness` object:

```json
{
  "freshness": {
    "state": "fresh" | "stale" | "unknown",
    "market_timestamp": "2026-09-02T10:30:00Z",
    "fetched_at": "2026-09-02T10:35:00Z",
    "threshold_minutes": 15,
    "source": "mock",
    "warnings": []
  }
}
```

When `state` is `stale` or `unknown`, the response must include a warning. A request with `?strict_fresh=true` must fail with `422` if the freshest available data is stale.

## Pagination

List endpoints accept `page` (1-indexed) and `page_size` (default 20, max 100). Cursor pagination may be adopted later for very large history or document lists. Always return `total` when cheap to compute.

## Endpoint contracts

### Health

- `GET /api/v1/health/live` — liveness, no dependencies.
- `GET /api/v1/health/ready` — readiness: database, migrations, required extensions.
- `GET /api/v1/health/ollama` — Ollama availability and installed models.
- `GET /api/v1/health/providers` — provider status and last successful refresh per provider.

### Portfolio

- `GET /api/v1/portfolio/summary`
  - Returns total value, cash, number of holdings, today P&L, total P&L, largest position, and sector allocation.
  - Includes `as_of` and `currency`.

- `GET /api/v1/portfolio/holdings`
  - Returns list of holdings: symbol, quantity, average cost, current price, market value, unrealized P&L, realized P&L, allocation percent.

- `POST /api/v1/portfolio/transactions`
  - Creates a transaction.
  - Body: `stock_id` or `symbol`, `transaction_type`, `quantity`, `price`, `fees`, `amount`, `transaction_date`, `notes`.
  - Validation: `transaction_type` enum, `quantity` positive where applicable, `price` positive for BUY/SELL, no oversell, cash sufficiency, same-day ordering consistent.
  - Returns created transaction and updated holding.

- `GET /api/v1/portfolio/transactions`
  - Returns paginated transactions.
  - Supports `symbol`, `type`, `start_date`, `end_date` filters.

- `GET /api/v1/portfolio/transactions/{transaction_id}`

- `PUT /api/v1/portfolio/transactions/{transaction_id}`
  - Only allowed before settlement or with documented restrictions. Editing settled transactions requires reversing and re-posting.

- `DELETE /api/v1/portfolio/transactions/{transaction_id}`
  - Allowed only before settlement or with explicit reversal rules.

### Stocks

- `GET /api/v1/stocks`
  - List active stocks.
  - Supports `sector`, `search` (name/symbol prefix), pagination.

- `GET /api/v1/stocks/{symbol}`
  - Returns `symbol`, `name_ar`, `name_en`, `sector`, `currency`, `exchange`, `is_active`.

### Market data

- `GET /api/v1/stocks/{symbol}/quote`
  - Returns `open`, `high`, `low`, `close`, `volume`, `currency`, `market_timestamp`, `fetched_at`, `source`, `freshness`.
  - Query: `?strict_fresh=true` to require fresh data.

- `GET /api/v1/stocks/{symbol}/history`
  - Returns list of OHLCV bars.
  - Query: `start`, `end`, `interval` (default `1d`).
  - Includes `freshness` for the overall window.

- `GET /api/v1/stocks/{symbol}/volume`
  - Returns latest volume and average volume over a configurable window.

### Financials

- `GET /api/v1/stocks/{symbol}/financials`
  - Returns latest `financial_statements` row: revenue, gross profit, operating profit, net income, EPS, assets, liabilities, equity, cash, cash flows.
  - Includes `published_at`, `source`, `freshness`.

- `GET /api/v1/stocks/{symbol}/financials/snapshot`
  - Returns deterministic ratios: `pe`, `pb`, `roe`, `roa`, `debt_to_equity`, `profit_margin`, `revenue_growth`, `earnings_growth`, `dividend_yield`.
  - Ratios are computed from persisted statement data and the latest quote snapshot.
  - Missing/zero-denominator values are returned as `null` with a warning.

### Technical analysis

- `GET /api/v1/stocks/{symbol}/technical`
  - Returns `rsi_14`, `sma_20`, `sma_50`, `sma_200`, `macd`, `signal`, `volume`.
  - Values are `null` when the requested history is insufficient.
  - Includes `as_of` and history window metadata.

### Documents

- `GET /api/v1/documents`
  - Paginated list by `symbol`, `document_type`, `language`, `published_after`, `published_before`.

- `GET /api/v1/documents/{document_id}`
  - Returns metadata and a signed/local content URL or extracted text, never raw binary over JSON.

- `POST /api/v1/documents`
  - Upload or import a document.
  - Body: `symbol`, `document_type`, `title`, `language`, `published_at`, `source_url`, and file or content.
  - Triggers extraction, normalization, and chunking.

- `GET /api/v1/documents/{document_id}/chunks`
  - Returns chunks with metadata.

### RAG / search

- `POST /api/v1/search`
  - Body: `query`, `symbol` (optional), `document_type` (optional), `published_after` (optional), `limit` (default 5).
  - Returns ranked chunks with `document_id`, `chunk_index`, `title`, `source`, `published_at`, `page_or_section`, `score`, and an excerpt.

### Analysis

- `POST /api/v1/analysis/stock/{symbol}`
  - Body optional: `horizon`, `risk_profile`.
  - Returns the structured five-dimension analysis defined in [09 — Financial Safety](09-financial-safety.md) and Phase 07, including `recommendation`, `confidence` out of 100, `reasons`, `risks`, `missing_information`, `data_as_of`, and `sources`.

- `POST /api/v1/analysis/portfolio`
  - Returns portfolio-level analysis, risk concentration, and allocation.

### Chat

- `POST /api/v1/chat`
  - Body: `conversation_id`, `messages` (or single `message`).
  - Response: `message` (text), `tool_calls` executed, `data_as_of`, `sources`, `status`.
  - Streaming is optional in the first implementation; if implemented, use server-sent events with a documented frame format.

### Settings

- `GET /api/v1/settings`
  - Returns non-sensitive configuration values and current provider selection.

- `PUT /api/v1/settings/risk-limits`
  - Updates `max_single_position_percent`, `max_sector_exposure_percent`, `min_cash_percent`.
  - Must be persisted and reconciled by the risk engine.

### Trade prohibition

- No endpoint may create, route, or execute a trade order.
- No endpoint may hold brokerage credentials.
- Any future `POST /orders` or similar must be explicitly out of MVP scope and documented as a decision.

## Validation errors

Validation errors return `400` or `422` with a list of field-level issues:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Request validation failed.",
    "details": [
      { "field": "quantity", "message": "Quantity must be positive." }
    ]
  },
  "meta": { ... }
}
```

## Correlation IDs

The API generates a `request_id` per request and returns it in `meta.request_id`. Clients may supply `X-Request-ID` to propagate the correlation. Log all requests with the correlation ID and route path; do not log bodies or query parameters that may contain secrets.

## Versioning

URL path versioning (`/api/v1`). Future breaking changes move to `/api/v2`. Deprecation uses response headers and documentation, not silent changes.

## Acceptance checklist

- [ ] All endpoints return the standard envelope.
- [ ] Every data endpoint includes freshness/source/timestamp metadata.
- [ ] Market, financial, technical, and chat endpoints fail gracefully on stale data when `strict_fresh=true`.
- [ ] List endpoints support pagination.
- [ ] Error responses use safe, non-leaky messages.
- [ ] Correlation IDs propagate to logs.
- [ ] No endpoint exists for trade execution in the MVP.
- [ ] UI receives only the API contract, never raw database or provider details.
- [ ] API version is stable and documented.
