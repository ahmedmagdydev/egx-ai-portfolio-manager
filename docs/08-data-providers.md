# 08 — Data Providers

## Purpose

This document defines the market-data provider interface, the validation required before any public web source can be trusted, the mandatory mock/fixture strategy, fallback and replacement behavior, and the public-source research matrix. It does not implement any adapter or schedule live scraping.

## Scope

The target source for EGX market data is a public web source, but no source may be declared production-safe until legality/terms, stability, coverage, timestamps, currency, rate limits, and freshness have been validated. Mock and fixture providers are mandatory even after a public source is adopted. The application must work offline with fixtures.

## Provider interface

All market-data consumers interact with an abstraction, not a source. The protocol defines:

```python
class MarketDataProvider(Protocol):
    async def get_quote(self, symbol: str) -> Quote: ...
    async def get_historical_prices(
        self, symbol: str, start: datetime, end: datetime, interval: str = "1d"
    ) -> list[Bar]: ...
    async def get_volume(self, symbol: str) -> VolumeSummary: ...
    def get_status(self) -> ProviderStatus: ...
```

Return objects must carry:

- `symbol` (normalized)
- `currency` (`EGP` unless proven otherwise)
- `market_timestamp` (observed market time in UTC)
- `fetched_at` (retrieval time in UTC)
- `source` identifier
- `freshness` state (`fresh`, `stale`, `unknown`)
- `interval` for historical bars

The adapter is responsible for normalization, validation, and failure handling.

## Provider implementations

### `MockMarketDataProvider`

- Deterministic.
- Returns pre-defined OHLCV bars and quotes for a small set of symbols (e.g., `COMI`, `FWRY`, `EAST`).
- Supports controllable clock and stale/missing/malformed modes for tests.
- Does not use the network.
- Used for CI, local development, and tests by default.

### `ManualCSVProvider`

- Reads user-provided CSV or JSON files from `IMPORTS_DIR`.
- Validates schema, dates, and OHLCV invariants.
- Useful for manual experiments, historical research, and offline work.

### `OanorEgxProvider` (real web adapter — opt-in)

- Implements the `MarketDataProvider` interface against the **Oanor EGX API** (`https://api.oanor.com/egx-api`), a gateway that returns EGX live quotes and screener data.
- Requires a free Oanor API key (`OANOR_API_KEY`) stored in `.env`.
- Default is the mock provider; Oanor is enabled only when `MARKET_DATA_PROVIDER=oanor`.
- Currently implemented for live quote and volume. Historical OHLCV is sourced from the companion **Oanor Finance API** (`/finance-api/v1/history`) using a configurable exchange suffix (default `.CA`).
- **Not declared production-ready**: upstream data is attributed to TradingView, and the upstream terms restrict non-display / machine-driven usage. It is suitable for local, human-readable decision support only until a full legal review is completed.

### `PublicWebProvider` (placeholder name)

- Generic placeholder retained for future validated sources. The Oanor adapter above is the first concrete implementation of this slot.

## Validation spike criteria

Before `PublicWebProvider` can be enabled for anything beyond manual opt-in tests, produce a written validation report covering:

1. **Legality and terms**
   - Is the source publicly accessible without authentication or credential sharing?
   - Does the site publish Terms of Use, robots.txt, or an API policy?
   - Does accessing the data programmatically require explicit permission?
   - Is redistribution to a local database permitted?
   - Is there a prohibition on automated access?

2. **Stability**
   - Has the page/endpoint URL changed historically?
   - Does the response format (HTML, JSON, embedded JS) change frequently?
   - Does the site use anti-bot measures (CAPTCHA, rate limits, token rotation, obfuscation)?

3. **Coverage**
   - Which EGX-listed symbols are available?
   - Is coverage limited to active or liquid stocks?
   - What historical depth is available (days, months, years)?
   - Is intraday data available or only end-of-day?

4. **Timestamps**
   - What timezone is displayed and published?
   - Are timestamps in local Cairo time, UTC, or an ambiguous local offset?
   - Is there a delay (e.g., 15 minutes) relative to live trading?
   - How are non-trading days, holidays, and suspended stocks represented?

5. **Currency**
   - Are all prices in EGP?
   - Is there any FX-denominated instrument?
   - How are currency values formatted (decimal separator, thousands separator)?

6. **Rate limits and politeness**
   - Does the site publish a request rate limit?
   - What is a safe per-second request budget?
   - Is there a daily or hourly cap?
   - What headers are expected (`User-Agent`, `Accept`, `Referer`)?

7. **Data quality and parsing risk**
   - Compare a sample of symbols and dates against a second public reputable source.
   - Document discrepancies in OHLCV, volume, or timestamp.
   - Document how corporate actions (splits, dividends, capital increases) are handled.
   - Document how Arabic/English company names and sectors are represented.

8. **Provenance**
   - Record exact URL, fetched timestamp, and checksum.
   - Preserve a small sample in `data/raw/` or fixtures for regression testing.

Only after the report is reviewed and accepted can the source be enabled by default. Until then, mock/fixture mode remains the default.

## Public-source selection matrix

This matrix must be filled during the validation spike. Example rows:

| Source                                   | Legal OK | Stable URL/Format | EGX Coverage            | Timestamps clear | EGP-only     | Rate limit known | Sample cross-check | Status    |
| ---------------------------------------- | -------- | ----------------- | ----------------------- | ---------------- | ------------ | ---------------- | ------------------ | --------- |
| EGX official website                     | TBD      | TBD               | TBD                     | TBD              | TBD          | TBD              | TBD                | candidate |
| Mubasher / investing sites               | TBD      | TBD               | TBD                     | TBD              | TBD          | TBD              | TBD                | candidate |
| Yahoo Finance EGX tickers (e.g. COMI.CA) | no       | medium            | broad                   | UTC/Eastern      | yes          | no hard cap      | not validated      | rejected  |
| Oanor EGX API (TradingView upstream)     | review   | high              | quote/screener          | UTC              | yes          | yes              | not yet performed  | opt-in    |
| Oanor Finance API (/v1/history)          | review   | high              | global (EGX suffix TBD) | UTC              | yes          | yes              | not yet performed  | opt-in    |
| Manual CSV import                        | yes      | n/a               | user-defined            | user-defined     | user-defined | n/a              | user-responsible   | fallback  |
| Mock provider                            | yes      | yes               | limited                 | controlled       | EGP          | n/a              | yes                | default   |

No source may be marked `production-ready` in this matrix until all its cells are `yes` or `n/a` and a sample cross-check passes.

## Adapter behavior

1. All network requests have connect/read timeouts and a bounded retry policy for idempotent reads.
2. Rate limiting is enforced client-side, never bypassed.
3. Parsing failures raise typed errors; raw responses may be quarantined for diagnosis.
4. Success and failure are both recorded with provenance.
5. If a public source fails repeatedly, the adapter falls back to the last cached record and marks it `stale`. It does not invent or interpolate missing bars.
6. Currency values are normalized to ISO-style `EGP`.
7. Timestamps are parsed with explicit timezone and converted to UTC for storage.
8. Symbol mapping is explicit; aliases and prefixes are resolved in a configuration layer, not hard-coded in the adapter.

## Fixture and mock requirements

1. Fixtures contain sanitized OHLCV for selected symbols across a known date range.
2. Fixtures are versioned and checksummed.
3. Tests run against the mock provider and fixture replay, not the live source.
4. CI pipelines never depend on live public sources.
5. Real-source tests are opt-in and marked; failures do not break the default build.

## Replacement and fallback policy

- The `MARKET_PROVIDER` setting selects the active adapter.
- Consumers always call the provider abstraction; they do not know which adapter is active.
- A future public source adapter replaces `PublicWebProvider` by implementing the same interface.
- If the active provider becomes unavailable, the consumer receives a typed `MarketDataUnavailable` error. The UI shows the last-known `stale` data with a warning.

## Manual import

Users may drop CSV/JSON files into `IMPORTS_DIR`. The manual provider reads and validates them. Imported data must include `symbol`, `timestamp`/`date`, `open`, `high`, `low`, `close`, `volume`, `currency`, `source` label, and an optional `source_url`. Invalid rows are rejected with a row-level report.

## Oanor EGX API validation notes

Research performed: 2026-09-03.

### Legality and terms

- Oanor marketplace terms (https://www.oanor.com/terms) state that providers are responsible for lawful upstream services and that access requires a valid key and subscription.
- The EGX API endpoint metadata lists its upstream source as the **TradingView public screener** (`scanner.tradingview.com/egypt/scan`).
- TradingView terms (https://www.tradingview.com/policies/) explicitly restrict **non-display usage** of its market data: prohibited uses include automated/algorithmic decision-making, price referencing in operations, and creating products based on TradingView content.
- The current application is a **local, single-user, human-readable decision-support tool** that does not trade automatically or redistribute data. This is likely display-only internal use, but a final legal review is required before marking the source production-ready.

### Stability

- REST endpoints are versioned (`/v1/quote`, `/v1/screener`, `/v1/index`, `/v1/meta`).
- Response envelope is stable: `{ data, meta, status, message, success }`.
- Authentication is a single header (`x-oanor-key`).

### Coverage

- Quote endpoint returns price, change, open/high/low, volume, market cap, P/E, sector, company name, currency.
- History endpoint is not offered by the EGX API itself; the companion Finance API (`/finance-api/v1/history`) provides OHLCV candles for global tickers. EGX symbol mapping for history (e.g. `COMI.CA`) has not yet been verified.

### Timestamps

- Meta timestamps are ISO-8601 UTC.
- Quote data does not include an explicit market timestamp; we use the API meta timestamp as `fetched_at` and treat the quote as observed at the last known close for freshness calculations.

### Currency

- All EGX quote values are returned in EGP.

### Rate limits

- Free tier: 12,200 calls/month and 2 requests/second for the EGX API; 800 calls/month and 1 request/second for the Finance API.
- The adapter enforces a client-side 1-second cooldown and respects HTTP 429 responses.

### Recommended configuration

```env
MARKET_DATA_PROVIDER=oanor
OANOR_API_KEY=oanor_live_...
OANOR_BASE_URL=https://api.oanor.com
OANOR_HISTORY_SYMBOL_SUFFIX=.CA
```

### Status

Recommended for **opt-in local use only**. Not production-ready until:

- a sample cross-check against a second reputable EGX source is performed,
- history symbol mapping is confirmed,
- and the TradingView upstream terms are reviewed for this specific use case.

## Corporate actions

MVP does not adjust historical prices for splits, dividends, or capital increases automatically. Raw prices are stored. If an adjusted series is available from a validated source, store both `close` and `adjusted_close` with explicit labels. Never mix adjusted and raw series in the same calculation.

## Acceptance checklist

- [ ] `MarketDataProvider` protocol and DTOs are defined.
- [ ] `MockMarketDataProvider` is deterministic and fixture-driven.
- [ ] `ManualCSVProvider` supports validated user imports.
- [ ] No public source is enabled by default until the validation spike is accepted.
- [ ] Validation report covers legality, stability, coverage, timestamps, currency, rate limits, and sample cross-check.
- [ ] Public-source matrix is completed and reviewed.
- [ ] Network adapter uses bounded timeouts, retries, and client-side rate limits.
- [ ] Cached `stale` data is never relabeled as `fresh`.
- [ ] Default test suite runs offline against mock/fixtures.
- [ ] Real-source tests are opt-in and do not block CI.
- [ ] Currency and timestamp normalization are explicit and audited.
