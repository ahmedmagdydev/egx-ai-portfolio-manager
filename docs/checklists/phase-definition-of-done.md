# Phase Definition of Done Checklist

Use this checklist before marking any implementation phase complete. A phase is **done** only when every item is checked, the evidence column is filled, and a reviewer has signed off.

---

## General Phase Exit Criteria

| # | Criterion | Evidence / Location | Checked | Reviewer |
|---|-----------|---------------------|---------|----------|
| 1 | Phase prerequisites are satisfied (previous phases, tests, infrastructure). | | ☐ | |
| 2 | All ordered tasks in the phase document are complete. | | ☐ | |
| 3 | Code compiles/starts without errors in the local development environment. | | ☐ | |
| 4 | Unit tests for the phase pass (`pytest` / `npm test`). | | ☐ | |
| 5 | Integration tests for the phase pass (database, providers, LLM where applicable). | | ☐ | |
| 6 | Manual demo script from the phase document was executed and passed. | | ☐ | |
| 7 | API contracts are documented and match the schemas described in the phase. | | ☐ | |
| 8 | Data models and migrations are documented. | | ☐ | |
| 9 | Errors are handled and tested, including failure scenarios listed in the phase. | | ☐ | |
| 10 | Safety and failure behavior from the phase document is implemented and verified. | | ☐ | |
| 11 | No automatic trade execution or order placement is introduced. | | ☐ | |
| 12 | Arabic/RTL UX items from the phase document are implemented and visually tested. | | ☐ | |
| 13 | LLM numerical facts are sourced from deterministic tools/calculations, not generated. | | ☐ | |
| 14 | Logs and audit trails are implemented without leaking credentials or PII. | | ☐ | |
| 15 | Phase artifacts listed in the phase document exist in the repository. | | ☐ | |

---

## Phase-Specific Exit Criteria

### Phase 07 — Portfolio AI

| # | Criterion | Evidence | Checked | Reviewer |
|---|-----------|----------|---------|----------|
| 1 | `PortfolioAnalysisResponse` schema is implemented and validated. | | ☐ | |
| 2 | Single-stock analysis endpoint returns structured recommendations. | | ☐ | |
| 3 | Whole-portfolio analysis endpoint returns top-level and per-holding assessments. | | ☐ | |
| 4 | System prompt is versioned in `docs/prompts/portfolio-analysis-v1.md`. | | ☐ | |
| 5 | Recommendation enum restricted to BUY/ACCUMULATE/HOLD/REDUCE/SELL/WATCH. | | ☐ | |
| 6 | Confidence displayed as `/100`, never as a probability of return. | | ☐ | |
| 7 | Every analysis includes `data_as_of` and source citations. | | ☐ | |
| 8 | Forbidden-phrase guard rejects guaranteed-return/probability language. | | ☐ | |
| 9 | Arabic recommendation card renders RTL with correct labels. | | ☐ | |
| 10 | Stale or missing data is surfaced in `missing_information`. | | ☐ | |
| 11 | Analysis endpoint returns 503 when Ollama is unavailable. | | ☐ | |
| 12 | AI analysis log table records requests, tool calls, and responses. | | ☐ | |

### Phase 08 — Risk Engine

| # | Criterion | Evidence | Checked | Reviewer |
|---|-----------|----------|---------|----------|
| 1 | `RiskLimits` configuration is stored and editable without redeploy. | | ☐ | |
| 2 | Deterministic risk functions pass unit tests to 4 decimal places. | | ☐ | |
| 3 | `GET /api/risk/portfolio` returns a complete `RiskReport`. | | ☐ | |
| 4 | `GET /api/risk/stock/{symbol}` returns standalone and contribution risk. | | ☐ | |
| 5 | Position, sector, and cash limit breaches are detected and flagged. | | ☐ | |
| 6 | Volatility, drawdown, beta, Sharpe are computed or marked missing. | | ☐ | |
| 7 | Correlation matrix handles insufficient overlap correctly. | | ☐ | |
| 8 | Risk report is fed into AI analysis when `include_portfolio=True`. | | ☐ | |
| 9 | Rebalancing suggestions are read-only and informational. | | ☐ | |
| 10 | Arabic risk UI renders RTL; sector chart and badges flip correctly. | | ☐ | |
| 11 | Missing benchmark or price history is reported, not fabricated. | | ☐ | |

### Phase 09 — Dashboard

#### Stage A — Thin Portfolio UI

| # | Criterion | Evidence | Checked | Reviewer |
|---|-----------|----------|---------|----------|
| 1 | `/portfolio` shows summary, holdings, and sector allocation. | | ☐ | |
| 2 | Transaction add/edit/delete forms work and recalculate deterministically. | | ☐ | |
| 3 | Transaction history is filterable and consistent with holdings. | | ☐ | |
| 4 | `/settings` supports locale switch (ar/en) and risk limits display. | | ☐ | |
| 5 | Manual demo: add COMI, add fees, sell half, verify P&L and average cost. | | ☐ | |
| 6 | E2E Playwright tests for transaction CRUD pass. | | ☐ | |
| 7 | RTL visual regression test for `/portfolio` passes. | | ☐ | |
| 8 | Arabic numerals, dates (`DD/MM/YYYY`), and currency (`ج.م`) render correctly. | | ☐ | |

#### Stage B — Full Dashboard

| # | Criterion | Evidence | Checked | Reviewer |
|---|-----------|----------|---------|----------|
| 1 | `/dashboard` loads summary grid with portfolio value, P&L, cash, AI score. | | ☐ | |
| 2 | `/stocks` and `/stocks/[symbol]` display price, chart, financials, technicals, news, disclosures. | | ☐ | |
| 3 | Charts render correctly in LTR and RTL with EGP axis. | | ☐ | |
| 4 | `/analysis` shows AI stock and portfolio analysis cards with citations. | | ☐ | |
| 5 | `/risk` shows breaches, sector allocation, concentration, rebalancing ideas. | | ☐ | |
| 6 | `/documents` supports RAG search with ranked, cited results. | | ☐ | |
| 7 | Locale switcher preserves state and flips layout direction. | | ☐ | |
| 8 | All dashboard pages have passing component/unit tests. | | ☐ | |

### Phase 10 — AI Chat

| # | Criterion | Evidence | Checked | Reviewer |
|---|-----------|----------|---------|----------|
| 1 | Chat sessions and messages persisted in PostgreSQL. | | ☐ | |
| 2 | `POST /api/chat/sessions/{id}/messages` streams SSE events. | | ☐ | |
| 3 | Tool call, tool result, delta, and done events stream in correct order. | | ☐ | |
| 4 | System prompt versioned in `docs/prompts/chat-assistant-v1.md`. | | ☐ | |
| 5 | Intent routing selects correct tools for portfolio, stock, risk, document queries. | | ☐ | |
| 6 | Arabic queries produce Arabic responses; English queries produce English. | | ☐ | |
| 7 | Assistant refuses trade-execution and guaranteed-return requests. | | ☐ | |
| 8 | Every factual answer cites sources and timestamps. | | ☐ | |
| 9 | Chat UI is RTL in Arabic, LTR in English, with right-aligned Arabic bubbles. | | ☐ | |
| 10 | Session history survives refresh and page navigation. | | ☐ | |
| 11 | Evaluation dataset exists and harness runs. | | ☐ | |

### Phase 11 — Backtesting and Evaluation

| # | Criterion | Evidence | Checked | Reviewer |
|---|-----------|----------|---------|----------|
| 1 | Backtest engine accepts `as_of` date and filters all data sources. | | ☐ | |
| 2 | Look-ahead bias test passes (no future data in backtest runs). | | ☐ | |
| 3 | At least three backtest scenarios are defined and produce stored reports. | | ☐ | |
| 4 | Backtest metrics include return, drawdown, win rate, Sharpe, benchmark, turnover. | | ☐ | |
| 5 | AI evaluation harness runs a fixed question set in Arabic and English. | | ☐ | |
| 6 | Evaluation criteria cover numerical accuracy, tool usage, citations, no hallucination, reasoning, Arabic quality, timestamps, safety. | | ☐ | |
| 7 | Baseline evaluation report is saved in `eval-reports/`. | | ☐ | |
| 8 | At least one optimization cycle completed and pass rate stable or improved. | | ☐ | |
| 9 | Evaluation UI or CLI report is accessible to reviewers. | | ☐ | |

### Phase 12 — Release Readiness

See the dedicated `docs/checklists/release-checklist.md` for the final release checklist. The checklist below is a preview of items that must also pass per phase.

| # | Criterion | Evidence | Checked | Reviewer |
|---|-----------|----------|---------|----------|
| 1 | Investment, data-freshness, AI-limitation, and privacy disclaimers implemented. | | ☐ | |
| 2 | User cannot bypass first-launch disclaimer. | | ☐ | |
| 3 | README and user guide exist in English and Arabic. | | ☐ | |
| 4 | `.env.example` is complete; no secrets committed. | | ☐ | |
| 5 | Performance validated on target hardware. | | ☐ | |
| 6 | Final test suite passes with no release-blocking failures. | | ☐ | |
| 7 | Security review signed off. | | ☐ | |
| 8 | RTL/Arabic review signed off. | | ☐ | |
| 9 | Docker Compose or start script runs from fresh clone. | | ☐ | |
| 10 | Release notes written and version tag created. | | ☐ | |

---

## Sign-Off

| Phase | Completed date | Reviewer name | Signature / link |
|-------|---------------|---------------|------------------|
| 07 Portfolio AI | | | |
| 08 Risk Engine | | | |
| 09 Dashboard Stage A | | | |
| 09 Dashboard Stage B | | | |
| 10 AI Chat | | | |
| 11 Backtesting & Evaluation | | | |
| 12 Release Readiness | | | |

---

## Notes

- A phase cannot be marked complete if any release-blocking item is unchecked.
- Evidence should be a file path, test command output, screenshot link, or commit hash.
- If a criterion does not apply to a phase, mark it N/A and explain in the evidence column.
- Reversing an earlier phase decision may require updating the decision log (`docs/decision-log.md`) and re-checking affected phases.
