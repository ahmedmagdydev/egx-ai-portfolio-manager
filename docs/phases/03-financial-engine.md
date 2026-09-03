# Phase 03 — Financial Engine

## Objective
Store sourced EGX financial statements and calculate a reproducible financial snapshot in application code. The LLM must never invent or calculate ratios when reliable raw data exists.

## Prerequisites
- Phases 00–02 accepted; stock identity, quote provenance, Decimal conventions, and public-source validation process are stable.
- Accounting scope and units are explicit: consolidated versus standalone, annual versus quarterly, fiscal periods, reported currency, restatements, and per-share scale.
- Permitted public company/EGX disclosures are selected and cross-check procedure documented; deterministic fixtures exist.

## Expected modules and artifacts
- Financial statement models/schemas/migration, repository, ingestion/normalization and validation service.
- `backend/app/finance/` pure ratio/growth functions and snapshot assembler.
- Source adapter or manual import boundary plus `MockFinancialDataProvider`/fixtures.
- Financial snapshot API, lineage metadata, data-quality warnings, unit/integration/API tests, and hand-calculated golden cases.

## Schema/API changes
`financial_statements`: `id`, stock reference/`symbol`, `period_start` where available, `period`/`period_end`, `period_type`, `scope`, `currency`, `unit_scale`, `revenue`, `gross_profit`, `operating_profit`, `net_income`, `eps`, `assets`, `liabilities`, `equity`, `cash`, `operating_cash_flow`, `investing_cash_flow`, `financing_cash_flow`, `source`, `source_url`, `published_at`, `fetched_at`, `created_at`, plus restatement/version metadata. Numeric facts are nullable because statements differ. Unique/version rules must not silently replace prior filings.

Add a financial snapshot endpoint such as `GET /api/stocks/{symbol}/financials/snapshot?as_of=` returning symbol, period/scope/currency, price and price timestamp when valuation ratios are requested, each metric, source lineage, `data_as_of`, and warnings/missing fields. Distinguish `null/not_available` from numeric zero.

## Ordered tasks
1. Define normalized concepts, signs, units, period/scope enums, restatement policy, and formula specification with examples.
2. Add migration and strict import/Pydantic schemas; preserve source values and normalized values/lineage where practical.
3. Implement deterministic mock fixtures and ingestion pipeline. Validate public-source samples against original filings and a second public reference when available; discrepancies remain visible.
4. Implement pure Decimal calculations: P/E, P/B, ROE, ROA, debt-to-equity, profit margin, revenue growth, earnings growth, and dividend yield (only with sourced dividends).
5. Implement comparable-period selector and as-of filtering using `published_at`; never use a later publication in historical snapshots.
6. Assemble snapshot from one explicitly selected statement scope/period set and one phase-02 quote. Do not combine consolidated and standalone values or silently mix units/currencies.
7. Expose route and quality warnings; document formulas, annualization policy, rounding only at presentation, and unavailable cases.
8. Add deterministic golden tests and reconciliation against independent manual calculations.

## Algorithms and edge cases
- P/E = price/EPS only for compatible per-share currency/unit and a clearly labeled EPS basis; zero or negative EPS yields null/not meaningful, not infinity.
- P/B = market price/book value per share only when shares outstanding or sourced BVPS is available. Do not divide total equity by price.
- ROE/ROA use average beginning/end equity/assets when both are available; otherwise use documented fallback and warning. Zero/negative denominator is null or flagged.
- Debt-to-equity requires a defined debt concept; if only liabilities exist, label `liabilities_to_equity` rather than misname it. Negative/zero equity is not meaningful.
- Margin = net income/revenue; growth = `(current-prior)/abs(prior)` only for comparable period type, duration, scope, currency/unit, and accounting basis. Prior zero/missing means null.
- Dividend yield uses sourced trailing/declared dividend convention and timestamp-matched price; never infer dividends from cash flow.
- Restatements are versioned. Latest-known snapshot may use restated values; an `as_of` snapshot may use only versions published by that date. Preserve original publication dates to prevent look-ahead bias.
- Handle nulls, negative values, Arabic numerals/labels during parsing, thousand/million scales, parentheses negatives, fiscal-year changes, duplicate filings, currency changes, and rounding differences.

## Tests
- Unit/golden tests for every formula with exact Decimal outputs and null/not-meaningful cases.
- Period selector tests: annual vs quarter, comparable prior period, fiscal-year changes, consolidated vs standalone, restatement, and publication cutoffs.
- Ingestion tests for Arabic/English labels, unit scaling, negative formats, missing fields, duplicate/versioned documents, and malformed totals.
- Integration tests for constraints, lineage persistence, quote timestamp compatibility, and deterministic repeated snapshots.
- API tests for complete, partial, negative-earnings, no-price, stale-price, unknown stock, and `as_of` responses.
- Default tests use mocks/captured permitted fixtures; public checks are opt-in and results are reviewed, not silently accepted.

## Manual demo
1. Import a bilingual, sourced COMI fixture with two comparable periods and show retained source/publication/scope/unit metadata.
2. Retrieve a fixed mock price and generate the guide-style snapshot including P/E, P/B where inputs suffice, ROE, and growth.
3. Reconcile each displayed ratio by hand from raw facts; show full precision and presentation rounding policy.
4. Load a negative-EPS or zero-revenue case and demonstrate `not meaningful` rather than infinity/fabrication.
5. Add a restatement and compare latest-known with a historical `as_of` snapshot, proving no future filing leaks backward.

## Observability and failure handling
- Log source, filing identity/version, symbol, period/scope, publication/fetch timestamps, validation outcome, missing-field count, and safe error code; avoid logging private/manual notes.
- Data-quality warnings identify unit/currency mismatch, stale/missing quote, incomparable period, restatement, unsupported formula, and cross-source discrepancy.
- Failed imports are atomic and quarantined; previous validated statements remain available. Snapshot assembly degrades field-by-field rather than inventing values.

## Acceptance checklist
- [ ] Financial statement schema preserves provenance, period, scope, currency, units, and versions.
- [ ] Public-source samples are checked against filings/another public reference.
- [ ] All required metrics are deterministic, documented, and unit tested.
- [ ] Null, zero, negative, missing, and incomparable inputs are handled safely.
- [ ] Snapshot exposes timestamps, sources, warnings, and missing information.
- [ ] Restatements and `as_of` queries prevent silent replacement/look-ahead bias.
- [ ] Arabic/English ingestion fixtures round-trip correctly.
- [ ] The LLM and live network are unnecessary for calculation tests.

## Dependencies
- Upstream: phases 00–02.
- Downstream: phase 05 may ingest original filings; phase 06 exposes snapshots as facts.
- Does not depend on technical analysis, RAG, or Ollama.
