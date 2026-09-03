# Phase 02 — Market Data

## Objective
Introduce a swappable, validated market-data boundary for EGX quotes and OHLCV history, with provenance and freshness on every record. A deterministic mock is first-class; no endpoint may present stale or unverified data as current.

## Prerequisites
- Phases 00–01 accepted; stock symbols and Decimal/time conventions are stable.
- At least one legal public-source candidate has been researched manually. Its terms, access method, update cadence, symbol mapping, timezone, currency, and redistribution limits are documented before implementation.
- Freshness thresholds for quote and historical data are configured, not invented by the LLM.

## Expected modules and artifacts
- `backend/app/providers/market_data.py`: provider protocol/abstract class.
- `EGXProvider` (name may reflect the approved public source) and `MockMarketDataProvider`.
- Provider DTOs and validators, symbol mapper, ingestion/upsert service, cache/repository, and stock quote/history routes.
- `stock_prices` migration, provenance/freshness metadata, deterministic fixtures, provider contract tests, captured allowed samples, and a public-source validation report.
- Source-specific parsing remains isolated from domain/API schemas.

## Schema/API changes
`stock_prices`: `id`, stock reference/normalized `symbol`, `timestamp`, `open`, `high`, `low`, `close`, `volume`, `currency`, `source`, `source_url` or source record identifier where permitted, `fetched_at`, `created_at`; unique key on source/symbol/timestamp. Add validation/status fields if rejected/quarantined records are retained. Use Decimal OHLC, nonnegative volume, UTC instants, and indexes for latest quote/range reads.

Provider contract:
- `get_quote(symbol) -> Quote`
- `get_historical_prices(symbol, start, end) -> list[Bar]`
- `get_volume(symbol) -> Volume` (or derive from validated quote/bar while preserving the guide-facing method).
DTOs include `symbol`, values, `currency`, market timestamp, source, retrieval timestamp, and freshness state.

API:
- `GET /api/stocks/{symbol}/quote`
- `GET /api/stocks/{symbol}/history?start=&end=&interval=`
Responses include `source`, `market_timestamp`, `fetched_at`, `currency`, `freshness` (`fresh`, `stale`, `unknown`), threshold/as-of metadata, and warnings. Stale data may be returned only when explicitly labeled; strict-current requests fail with a typed status.

## Ordered tasks
1. Define provider/domain DTOs and error taxonomy independent of HTTP and any source library.
2. Document public-source validation: compare a small symbol/date sample against a second public official/reputable display, record URLs, timestamps, timezone, currency, corporate-action behavior, discrepancies, and terms. Do not scrape around access controls.
3. Implement a deterministic mock with fixed COMI and additional EGX fixtures, controllable clock, stale/missing/malformed modes, and no network.
4. Add migration, repository, idempotent upsert, and source precedence rules. Never silently overwrite a differing source record; retain provenance or flag conflict.
5. Implement the real adapter with bounded connect/read timeout, retry only for transient/idempotent reads, polite rate limiting, and strict payload validation.
6. Normalize source symbols, Arabic/English text if present, timestamps to UTC, and currency to ISO-style codes while retaining raw source identity.
7. Add freshness calculation and API routes. Wire phase-01 valuation to explicit quote snapshots, not hidden provider calls inside calculations.
8. Add scheduled/manual refresh entry point suitable for a local Windows process; prevent overlapping refreshes.
9. Complete contract, integration, and API tests using mocks/captured fixtures; real-source tests are opt-in and non-blocking.

## Algorithms and edge cases
- Validate `low <= open, close <= high`, all prices positive, volume nonnegative/integral where source semantics require it, timestamp plausible and not materially future-dated, known currency, and requested symbol match.
- EGX weekends, exchange holidays, suspended/illiquid stocks, delayed feeds, no-trade days, and source timestamps without timezone must not be mistaken for failure or freshness. Use exchange calendar/configured source semantics when available.
- Freshness is `as_of - market_timestamp` interpreted against trading sessions and source delay, not merely wall-clock age. `unknown` is safer than `fresh` when semantics are unclear.
- Deduplicate bars idempotently. Conflicting OHLCV from the same source/time is quarantined or versioned and logged; never silently replace old information.
- Range boundaries are explicit and consistent; reject `start > end`, unsupported interval, excessive range, unknown symbol, and malformed source data.
- Corporate-action adjusted versus raw prices must be labeled. Do not mix series. Decimal parsing must handle source separators without locale ambiguity.
- Circuit-break repeated source failures locally; serve last-known data only with a conspicuous stale warning and never relabel it current.

## Tests
- Provider contract suite runs identically against mock and adapter fixture replay.
- Unit tests for symbol/timezone/currency normalization, freshness across weekends/holidays, OHLCV invariants, deduplication, and stale-state calculation with frozen time.
- Integration tests for upsert idempotency, source conflicts, query ranges/order, transaction rollback, and phase-01 valuation using an explicit quote snapshot.
- API tests for fresh, stale, missing, unknown symbol, invalid range, upstream timeout/rate limit, and provenance fields.
- Fault injection for malformed HTML/JSON, partial payloads, DNS/timeout, 429, 5xx, changed source schema, and interrupted refresh.
- Opt-in public validation compares a small current sample and records differences; default suite is offline and deterministic.

## Manual demo
1. Start in mock mode; request COMI quote/history and show stable values, source, EGP, timestamps, and `fresh` state.
2. Advance the mock clock to show `stale`; request strict-current mode and show safe failure, then show labeled last-known data.
3. Value the phase-01 sample portfolio with that exact quote snapshot and reconcile the result.
4. If the public source is reachable and permitted, run a manual refresh, display provenance, and compare selected values to the source page plus a second public reference.
5. Simulate source outage and malformed data; prove cached data is not overwritten and no value is represented as current.

## Observability and failure handling
- Structured events include provider, source, normalized symbol, requested range, market/fetch timestamps, freshness, duration, retry count, record counts, and safe error code.
- Metrics/log summaries cover successes, validation rejects, stale serves, source conflicts, latency, rate limits, and last successful refresh. Do not log API keys or entire proprietary payloads.
- User-facing errors distinguish unavailable, stale, invalid upstream data, unsupported symbol/range, and internal persistence failure.
- Preserve the last validated record and raw evidence where legally permitted; quarantine bad input for diagnosis.

## Acceptance checklist
- [ ] Provider abstraction has real and deterministic mock implementations.
- [ ] Public-source legality, semantics, and sample cross-validation are documented.
- [ ] Quote/history APIs return structured provenance, currency, timestamps, and freshness.
- [ ] Stale/unknown data can never masquerade as current.
- [ ] Invalid/conflicting upstream records are rejected or quarantined without destroying validated data.
- [ ] Offline tests cover contracts and failure modes; live checks are opt-in.
- [ ] Phase-01 valuation receives explicit snapshots and remains deterministic.
- [ ] No LLM calculates, recalls, or repairs market values.

## Dependencies
- Upstream: phases 00–01.
- Downstream: phases 03–04 and 06 consume validated prices/history.
- Public sources are external optional dependencies; mocks remain sufficient for development and CI.
