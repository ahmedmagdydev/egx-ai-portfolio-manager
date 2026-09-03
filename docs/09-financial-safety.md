# 09 — Financial Safety

## Purpose

This document defines the safety rules that keep the EGX AI Portfolio Manager a decision-support research tool and protect the user from misleading outputs, stale data, and automated trading. It applies across the backend, API, UI, LLM prompts, and RAG retrieval.

## Role of the application

The application is an investment research and decision-support tool. It:

- does not execute trades automatically;
- does not provide personalized investment advice;
- does not guarantee returns;
- must distinguish facts from calculations, retrieval, interpretation, and opinion;
- must display data timestamps and sources;
- must warn when data is stale, incomplete, or missing.

## Deterministic source of truth

1. All numerical values shown to the user or used in analysis come from deterministic code, not from the LLM.
2. The LLM is provided with tool results and retrieved evidence. It reasons over them; it does not compute, estimate, or recall them from memory.
3. Ratios such as P/E, P/B, ROE, ROA, debt-to-equity, profit margin, revenue growth, and earnings growth are computed by deterministic services from validated `financial_statements` and `stock_prices`.
4. Technical indicators such as RSI, MACD, and moving averages are computed from historical OHLCV.
5. Portfolio values, P&L, allocations, and risk metrics are computed from the `transactions` ledger.

## Decimal and rounding policy

1. Store money and prices with at least four decimal places.
2. Store EPS and per-share values with at least eight decimal places.
3. Compute intermediate values with full precision; round only at presentation or API boundary.
4. Define and document the rounding mode (e.g., `ROUND_HALF_UP`) used at boundaries.
5. Never use `float` for money, quantities, prices, or ratios.

## Data freshness and staleness

1. Every market and financial data response includes `freshness.state`, `market_timestamp`, `fetched_at`, and `source`.
2. Freshness is computed against configured thresholds and exchange/session semantics, not a hard-coded clock.
3. Stale data is returned only with an explicit warning and the `stale` state.
4. A `strict_fresh` request fails safely rather than return stale data as current.
5. The UI displays `data_as_of` next to every number that depends on market data.

## Fact, calculation, retrieval, and opinion labels

The UI and AI responses must label information clearly:

- **Fact** — raw market data from a validated provider (e.g., last close price, volume).
- **Calculated** — deterministic computation from facts (e.g., P/E, P&L, RSI).
- **Retrieved** — text from a document or news source with citation.
- **Interpretation** — LLM reasoning over the above.
- **Opinion** — subjective assessment such as "attractive" or "risky".

Labels are present in API metadata and surfaced in the UI. The assistant uses qualifying language and avoids certainty about future prices.

## Recommendation language

Allowed recommendation values are:

- `BUY`
- `ACCUMULATE`
- `HOLD`
- `REDUCE`
- `SELL`
- `WATCH`

Confidence is expressed as `confidence: 72/100` or similar, never as a probability or guarantee. The structured response includes:

- `recommendation`
- `confidence`
- `valuation_assessment`
- `fundamental_assessment`
- `technical_assessment`
- `portfolio_assessment`
- `reasons`
- `risks`
- `missing_information`
- `data_as_of`
- `sources`

The model may not output any other action such as `EXECUTE` or `ORDER`.

## Citation rules

1. Every retrieved claim cites `source`, `title`, `published_at`, and `page/section` when available.
2. Every market/financial number cites the source and `data_as_of`.
3. Citations are structured data returned by the backend; the UI renders them consistently.
4. The LLM may not invent citations. If evidence is missing, it reports `missing_information`.

## Missing and incomplete data

1. When data is missing, the backend returns `null` with a warning and a reason code.
2. The model reports `missing_information` explicitly rather than fabricating values.
3. If a recommendation requires missing critical data, downgrade confidence or refuse a directional recommendation.
4. The UI shows the missing-data reason and prevents stale or incomplete analyses from being presented as definitive.

## Prohibition on automated trading

1. There is no endpoint or tool to place a buy or sell order.
2. `AUTO_TRADING_ENABLED` defaults to `false` and must remain `false` in the MVP.
3. If a prompt or document attempts to instruct the assistant to trade, the system prompt and tool registry refuse.
4. A disclaimer is shown in the UI and in every analysis/chat response: outputs are research, not investment advice.

## No guaranteed-return language

The system prompt, UI labels, and model output must avoid phrases such as:

- "guaranteed return"
- "risk-free"
- "will go up"
- "X% probability of profit" (unless from a calibrated, validated model)

Use phrasing like:

- "The current valuation ratios are lower than historical averages."
- "The portfolio concentration exceeds the configured limit."
- "Based on the available data, the recommendation is HOLD with moderate confidence."

## LLM system rules

The system prompt must include:

- "You are an Egyptian Stock Exchange investment research assistant."
- "You must not invent market data, financial figures, news, disclosures, prices, ratios, or portfolio information."
- "For current or numerical information, use the available tools."
- "Distinguish clearly between verified facts, calculated metrics, retrieved information, interpretation, and assumptions."
- "Never claim certainty about future stock prices."
- "Do not execute trades."
- "Recommendations are decision-support analysis, not guaranteed outcomes."
- "When evidence is insufficient, explicitly say the information is insufficient."
- "Always identify the date/time of market data used."
- "When using documents, cite the source and publication date."
- "When analyzing a stock for the user's portfolio, consider both the stock itself and its impact on the overall portfolio."

## Prompt and document injection resistance

1. Retrieved document content is treated as untrusted data.
2. Document text cannot override system instructions or tool rules.
3. User prompts are validated for length and suspicious instructions; attempted injection is logged and ignored.
4. Tool arguments are validated against schemas before execution.

## Currency assumptions

MVP is EGP-first and EGX-only. If a non-EGP instrument appears, report it as unsupported rather than silently convert. Multi-currency conversion is deferred to a later phase.

## Corporate actions

MVP does not automatically adjust for splits, dividends, capital increases, or rights issues. Raw prices and share quantities are authoritative. If the user enters a split manually, record it as a corporate-action transaction type or note. Support for automatic corporate actions is deferred.

## Acceptance checklist

- [ ] No numerical value originates from the LLM; the model only reasons over deterministic tool output.
- [ ] Money, prices, and ratios use Decimal types with documented precision and rounding.
- [ ] Every market/financial response carries freshness, source, and timestamp metadata.
- [ ] Stale data is clearly labeled and never returned as `fresh`.
- [ ] UI and AI outputs distinguish fact, calculation, retrieval, interpretation, and opinion.
- [ ] Recommendations use `confidence: X/100` and avoid probability/return guarantees.
- [ ] All citations include source, title, and publication date.
- [ ] Missing data is reported explicitly with `missing_information`.
- [ ] No tool or endpoint enables trade execution.
- [ ] System prompt contains the required safety rules.
- [ ] Document/user content cannot override system instructions.
- [ ] Disclaimers appear in UI and every analysis/chat response.
