# Phase 04 — Technical Analysis

## Objective
Compute a small, deterministic set of technical indicators from validated historical OHLCV: SMA 20/50/200, RSI 14, MACD, and volume. Provide transparent warm-up and data-quality behavior; add Bollinger Bands, ATR, volume indicators, and support/resistance only after the baseline is accepted.

## Prerequisites
- Phases 00–03 accepted; phase-02 history supplies ordered, provenance-bearing OHLCV with timezone, interval, adjustment, and freshness semantics.
- Formula conventions are frozen (close-based inputs, EMA seed, RSI smoothing, MACD 12/26/9, missing-session handling) before golden fixtures are generated.
- A reference library/version or independent spreadsheet is chosen solely to validate implementation outputs.

## Expected modules and artifacts
- `backend/app/technical/` pure series validators, indicator calculations, and snapshot assembler.
- Technical response schemas and `GET /api/stocks/{symbol}/technical` route.
- Fixed OHLCV fixtures (trending, flat, short, gapped, zero-volume), golden reference outputs, tests, formula documentation, and benchmark notes.
- Optional cache keyed by symbol, interval, adjustment mode, data end timestamp, and algorithm version; no mandatory new persistence table.

## Schema/API changes
No required database migration. If calculated results are cached/persisted, store algorithm name/version, parameters, source series identity/range, calculation timestamp, adjustment mode, and value; cached indicators can never lose input lineage.

`GET /api/stocks/{symbol}/technical?as_of=&interval=1d` returns symbol, interval, input source and last market timestamp, adjustment/freshness, observations, parameters, `rsi_14`, `sma_20`, `sma_50`, `sma_200`, `macd`, `signal`, optional histogram and latest volume, plus warnings. Unwarmed values are `null`, never zero. Historical `as_of` must truncate inputs before calculation.

## Ordered tasks
1. Publish exact formulas, parameter defaults, minimum observations, precision, EMA/RSI seed, ordering, duplicate, adjustment, and missing-bar policies.
2. Implement strict input normalization: one consistently adjusted daily series, ascending unique timestamps, finite Decimal/float-safe converted values, and OHLCV invariants.
3. Build pure SMA calculations and golden tests, then RSI (Wilder 14), then EMA/MACD (12, 26, 9), then volume output. Keep intermediate series testable.
4. Cross-validate fixtures against pinned `pandas-ta`/TA-Lib or independently generated reference, documenting expected seed-related differences rather than tuning silently.
5. Assemble the latest snapshot with lineage, observation count, freshness, warnings, and null warm-up fields.
6. Add API and optional deterministic cache invalidation when a bar is inserted/corrected or algorithm version changes.
7. Add performance tests for realistic local symbol histories; only then consider approved follow-up indicators.

## Algorithms and edge cases
- SMA(N) is arithmetic mean of the latest N valid closes and requires N observations.
- EMA uses `alpha=2/(N+1)` with the documented seed (prefer first N-period SMA). MACD is EMA12 minus EMA26; signal is EMA9 of the MACD series. Warm-up must account for both layers.
- RSI 14 uses Wilder-smoothed average gains/losses. Both zero implies a neutral/undefined policy documented consistently; zero average loss with gains yields 100, zero average gain with losses yields 0.
- Never forward-fill missing prices by default. A missing trading session is not a zero return; flag unexpected gaps against the exchange calendar. Duplicate bars are rejected or resolved by source version policy before calculation.
- Flat prices, splits/unadjusted discontinuities, suspended stocks, outlier bad ticks, zero volume, stale history, NaN/infinity, insufficient 20/50/200 samples, and mixed intervals/adjustment modes produce explicit warnings/nulls.
- Compute in chronological order but return only requested/latest values. Do not round intermediate values; declare output rounding. `as_of` excludes later prices to prevent look-ahead.
- Indicators describe history and are not standalone buy/sell recommendations.

## Tests
- Golden unit tests for SMA, RSI, EMA, MACD/signal, and volume, with tolerances justified against reference precision.
- Edge fixtures for exactly N and N-1 rows, constant/up/down series, duplicates, reversed order, missing dates, NaN/infinity, invalid OHLC, zero volume, and split-like discontinuity.
- Property checks: SMA of constant series equals constant; RSI remains 0–100; output timestamps never exceed `as_of`; repeated inputs yield identical results.
- Integration/API tests with `MockMarketDataProvider`, stale history, corrected bar/cache invalidation, unknown symbol, and insufficient history.
- No public network in default tests. Optional public-source sample comparison verifies inputs first and then indicators against an independent reference.

## Manual demo
1. Load a fixed 250+ day COMI mock series and call the technical endpoint.
2. Show SMA20/50/200, RSI14, MACD/signal, volume, input source, last timestamp, parameters, and freshness.
3. Compare selected latest values with the pinned reference tool/spreadsheet within documented tolerance.
4. Repeat with only 30 observations and show valid short-window values plus null SMA50/200 warnings.
5. Introduce a duplicate/bad bar and demonstrate rejection; run an earlier `as_of` and prove later bars are excluded.

## Observability and failure handling
- Log symbol, source-series identity, interval, adjustment mode, range, observation count, algorithm version, duration, cache status, warnings, and safe failure code.
- Distinguish invalid input, insufficient history, stale history, unsupported interval, and computation failure. Never substitute a prior indicator as current without stale labeling.
- Keep enough lineage to reproduce every output; corrections invalidate affected cached results. Avoid dumping full price histories in routine logs.

## Acceptance checklist
- [ ] Formula/seed/warm-up/rounding conventions are documented.
- [ ] Baseline indicators are deterministic and validated independently.
- [ ] API reports provenance, parameters, data timestamp, freshness, and warnings.
- [ ] Insufficient/invalid data produces nulls or typed errors, never misleading zeros.
- [ ] `as_of` prevents future data leakage.
- [ ] Mock-driven unit/integration/API suites pass offline.
- [ ] Corrected inputs invalidate derived outputs reproducibly.
- [ ] No LLM computes indicators or turns one indicator into guaranteed advice.

## Dependencies
- Upstream: phase 02 is required; phases 00–01 provide platform/stock identity. Phase 03 is sequencing context but not a calculation dependency.
- Downstream: phase 06 exposes technical facts to tools.
- Follow-up indicators depend on baseline acceptance and a demonstrated requirement.
