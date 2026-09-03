# Product Scope

## Purpose

Build a local-first, single-user research assistant for an individual managing Egyptian Exchange (EGX) investments. The product records portfolio activity, calculates financial outcomes deterministically, organizes market/company evidence, and uses a local language model to explain that evidence in Arabic or English.

It supports decisions; it does not make or execute them. The product must communicate uncertainty, freshness, provenance, and missing evidence rather than imply certainty.

## Source and assumptions

This scope interprets the [original guide](../EGX_AI_Portfolio_Manager_Implementation_Guide.md) under the approved documentation plan. The following assumptions are binding for the MVP unless deliberately revised:

- one trusted user on one local machine;
- EGX-listed equities only;
- EGP-first storage and presentation, with no production FX conversion;
- no authentication, authorization roles, tenancy, or cloud deployment;
- no external LLM API needed for basic functionality;
- no order-routing or brokerage integration;
- public-web market data is a target, not an already validated source;
- manual/fixture data and a mock provider remain supported for deterministic development and degraded operation.

## Primary persona and jobs

**Primary persona:** an Arabic- and/or English-speaking individual investor who understands that analysis is not a guarantee and wants private, locally processed portfolio research.

The user needs to:

1. record stocks, cash activity, fees, dividends, purchases, and sales;
2. inspect holdings, average cost, market value, realized/unrealized P&L, cash, and allocations;
3. inspect timestamped price history, financial statements/ratios, and a focused set of technical indicators;
4. find and cite evidence in company reports, disclosures, announcements, and news;
5. ask portfolio-aware questions in Arabic or English;
6. receive structured analysis across valuation, fundamentals, technicals, risk, and portfolio fit;
7. understand stale data, missing inputs, assumptions, concentration, and model limitations;
8. evaluate recommendations retrospectively without look-ahead bias.

A developer/operator is a secondary persona responsible for local setup, data-provider validation, backups, model health, and troubleshooting.

## MVP capabilities

### Deterministic portfolio core

- Stocks identified by a normalized EGX symbol and bilingual display names.
- Transaction types: `BUY`, `SELL`, `DIVIDEND`, `DEPOSIT`, `WITHDRAWAL`, and `FEE`.
- Holdings and cash derived from an auditable transaction history.
- Average cost, fees, realized/unrealized and daily/total P&L, market value, portfolio allocation, and sector allocation.
- Explicit validation for oversells, insufficient cash policy, same-day ordering, nonpositive values, duplicate submissions, and unsupported events.
- Decimal arithmetic and documented rounding; raw precision retained where practical and presentation rounding kept separate.

### Evidence layers

- Replaceable market-data interface for quotes, OHLCV history, and volume.
- Mock adapter and sanitized recorded fixtures mandatory for tests.
- Any public adapter adopted only after reviewing permission/access terms, robots policy where relevant, coverage, timestamp/currency semantics, delay, rate limits, historical depth, stability, and parser maintenance risk.
- Financial statement storage and deterministic calculations for valuation, profitability, leverage, growth, and dividends.
- Initial technical set: SMA 20/50/200, RSI 14, MACD, and volume; additional indicators require a demonstrated user need.
- Bilingual reports, statements, disclosures, announcements, and news preserved with original source and publication date.
- RAG retrieval with company/date/type filters and citations to source/title/date/page or section.

### AI-assisted analysis

- Local Qwen reasoning and embedding models through isolated provider interfaces.
- Typed tools—not model memory—for current prices, portfolio facts, ratios, indicators, risks, news, and document search.
- Structured recommendation values: `BUY`, `ACCUMULATE`, `HOLD`, `REDUCE`, `SELL`, or `WATCH`.
- “Analysis confidence: N/100” may summarize evidence quality; it must not be called a probability unless calibrated as one.
- Explicit lists of reasons, risks, missing information, evidence sources, and analysis/data timestamps.
- Safe refusal/degradation when a provider, database, retrieval pipeline, or model is unavailable.

### User interface

- Portfolio/dashboard, stocks and stock detail, analysis, documents, settings, and AI chat experiences.
- Responsive desktop-first interface suitable for local use.
- Visible freshness and source states beside material figures; stale, loading, missing, partial, and error states may not be encoded by color alone.

## Arabic, English, and RTL requirements

Arabic is a first-class product language, not translated decorative text.

- The application must support switching between Arabic (`ar-EG`) and English (`en`) without losing user state.
- Set `lang="ar"` and `dir="rtl"` at the document/container level for Arabic; use `lang="en"` and `dir="ltr"` for English.
- Layout must mirror logically in RTL: navigation, breadcrumbs, panels, alignment, directional icons, table flow, drawers, and keyboard focus order. Use CSS logical properties rather than hard-coded `left`/`right` where possible.
- EGX symbols, formulas, code, URLs, ISO timestamps, and Latin source names should remain LTR inside isolated `dir="ltr"` or bidirectional-safe elements. Never reverse ticker characters.
- Arabic text and mixed Arabic/Latin rows must not reorder numbers, signs, currency, percentages, or parentheses ambiguously. Test positive and negative P&L, decimal values, dates, and `COMI`-style tickers.
- Localize labels, validation, empty/error/stale warnings, disclaimers, recommendation descriptions, and accessibility names—not only page titles.
- Use locale-aware display formatting while keeping API payloads locale-neutral. EGP must be clearly identified; input parsing must not guess ambiguous decimal/group separators.
- Charts retain chronological left-to-right axes unless a validated chart behavior supports otherwise; surrounding labels and controls follow the active direction. Tooltips must remain legible in mixed script.
- Arabic typography must be readable at all supported breakpoints. Text expansion, line height, wrapping, and truncation must be tested; critical warnings and sources may not be hidden by truncation.
- Screen-reader landmarks, heading order, form associations, keyboard navigation, focus visibility, and color contrast must work in both directions.
- User queries may be Arabic, English, or mixed. Responses should follow the requested/detected language while preserving exact symbols and citations.
- Fixed bilingual evaluation cases must assess Arabic financial terminology, factual equivalence across languages, RTL rendering, mixed-script behavior, and safe uncertainty wording.

Example Arabic safety copy suitable for UI validation:

<div lang="ar" dir="rtl">
هذا التحليل لأغراض البحث ودعم القرار فقط، وليس ضمانًا للعائد أو أمرًا بتنفيذ صفقة. تحقّق من مصدر البيانات وتاريخها قبل اتخاذ القرار.
</div>

## Explicitly out of scope for the MVP

- Automated or one-click trading, broker credentials, and order execution.
- Guaranteed-return predictions or autonomous portfolio management.
- Multi-user collaboration, authentication, role-based access, or hosted SaaS.
- Native mobile or voice applications.
- Non-EGX assets and robust multi-currency/FX accounting.
- Splits, rights issues, mergers, spin-offs, and other corporate-action accounting; such events must be marked unsupported rather than approximated.
- Tax advice or jurisdiction-specific tax-lot optimization.
- High-frequency or real-time trading infrastructure.
- Unvalidated scraping presented as reliable production data.
- Large-model/cloud fallbacks, advanced screening, alerts, calendars, Monte Carlo analysis, and macro/peer/scenario features.

## Safety and trust requirements

1. Numerical sources of truth are validated external records and deterministic services. The LLM only reasons over supplied facts.
2. Every current value carries source, observation time, retrieval time, currency, and freshness status where applicable.
3. Documents carry source, URL when available, language, publication time, and location metadata.
4. UI and AI output distinguish verified facts, calculated metrics, retrieved claims, interpretation, and assumptions.
5. Stale data is never labeled current. Missing data is never replaced by a model guess.
6. Portfolio limits come from user/configuration values, never model invention.
7. Retrieved text is untrusted and cannot issue system instructions, alter tool permissions, or trigger execution.
8. No sensitive credentials or private portfolio exports enter Git, prompts unnecessarily, telemetry, or logs.
9. Recommendations include risks, missing evidence, and a decision-support disclaimer.
10. The application has no capability that can execute a trade in the MVP.

## Success measures and acceptance scenarios

### First usable milestone

Given a fixed set of EGP transactions with fees and partial sales, the application produces repeatable holdings, cash, average cost, realized/unrealized P&L, and allocations; APIs and UI agree; automated golden tests prove the expected ledger results; no AI service is required.

### Reliable research snapshot

For a selected symbol, the user sees a normalized quote/history, financial snapshot, and initial technical indicators. Each figure is either available with provenance/freshness or explicitly unavailable/stale. Provider failure does not fabricate a value.

### Cited retrieval

For a question about a report or disclosure, retrieval returns relevant bilingual evidence with source/title/publication date and page/section where available. The answer distinguishes quoted evidence from interpretation.

### Portfolio-aware AI

For equivalent Arabic and English questions, the assistant invokes typed tools, considers all five decision dimensions, returns the approved structured recommendation vocabulary, cites evidence, reports data timestamps and missing information, and does not claim certainty or execute an action.

### Mature decision support

Point-in-time backtesting and fixed AI evaluations measure returns/risk, benchmark and costs, numerical accuracy, source correctness, tool use, hallucination, reasoning, and Arabic quality. Future information is excluded from historical analyses.

## Scope-change rule

A proposed feature must state its user benefit, data and privacy impact, architecture owner, deterministic/AI boundary, Arabic/RTL impact, test evidence, and milestone dependency. Deferred functionality stays deferred unless the scope document and relevant architecture/decision records are deliberately updated.

## Related documents

- [Documentation guide](README.md)
- [Architecture](01-architecture.md)
- [Technology decisions](02-technology-decisions.md)
- [Repository layout](03-repository-layout.md)
