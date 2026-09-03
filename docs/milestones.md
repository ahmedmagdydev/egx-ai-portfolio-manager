# Project Milestones

This document maps the implementation phases to observable, release-oriented milestones. Each milestone has a clear user outcome, acceptance criteria, and the phases it depends on. Milestones are derived directly from the EGX AI Portfolio Manager Implementation Guide.

---

## Milestone 0 — Environment and Foundation

**Goal:** Development environment, models, and database are ready for iterative backend work.

**User outcome:** None yet; this is an infrastructure milestone.

**Depends on:** Implementation Guide Phase 0 — Environment Setup.

**Acceptance criteria:**

- [ ] Git, Node.js, Python 3.11+, Docker Desktop, PostgreSQL + pgvector, NVIDIA drivers, and Ollama installed.
- [ ] `ollama pull qwen3.5:9b` completed and model responds locally.
- [ ] `ollama pull qwen3-embedding:4b-q4_K_M` completed and embeddings generated.
- [ ] `nvidia-smi` shows GPU and `ollama ps` shows model loaded.
- [ ] Docker Compose stack starts PostgreSQL and pgvector without errors.
- [ ] `.env.example` created and documented.

**Exit artifact:** `docs/LOCAL_SETUP.md` verified by a second developer.

---

## Milestone 1 — Working Portfolio Engine (First Working Milestone)

**Goal:** User can manage a portfolio through a thin UI before any AI is introduced.

**User outcome:** A user can add stocks, record BUY and SELL transactions, enter fees, and see holdings with correct average cost, market value, and unrealized P&L.

**Depends on:** Implementation Guide Phases 1–5 and Phase 9 Stage A (Thin Portfolio UI).

**Acceptance criteria:**

- [ ] PostgreSQL schema for `stocks`, `transactions`, `holdings`, `cash_accounts` is created.
- [ ] Deterministic portfolio calculation engine passes unit tests.
- [ ] REST endpoints for transactions and portfolio summary return correct values.
- [ ] Thin Next.js portfolio UI supports add/edit/delete transactions and view holdings.
- [ ] Sector allocation displayed for holdings.
- [ ] Arabic/RTL locale switcher works for the portfolio page.

**Exit artifact:** Signed-off Phase 09 Stage A exit gate checklist.

---

## Milestone 2 — Market, Financial, and Technical Data

**Goal:** Stock pages show reliable market, financial, and technical snapshots.

**User outcome:** A user can open a stock detail page and see price, chart, P/E, P/B, ROE, revenue growth, EPS growth, RSI, MACD, and moving averages.

**Depends on:** Implementation Guide Phases 2–4.

**Acceptance criteria:**

- [ ] `MarketDataProvider` abstraction with `EGXProvider` and `MockMarketDataProvider`.
- [ ] Quote and historical price endpoints return structured data with source and timestamp.
- [ ] Financial ratios are deterministic and unit-tested.
- [ ] Technical indicators (SMA 20/50/200, RSI 14, MACD) are deterministic.
- [ ] Stock detail page displays all required data fields.
- [ ] Data freshness badge warns when market data is stale.

**Exit artifact:** Signed-off Phase 09 Stage B stock-page checklist and test report.

---

## Milestone 3 — Document Ingestion and RAG

**Goal:** Users can ask questions about company reports and disclosures with source references.

**User outcome:** A user searches "ما سبب انخفاض صافي الدخل؟" and receives cited excerpts from the correct document and period.

**Depends on:** Implementation Guide Phases 5–6.

**Acceptance criteria:**

- [ ] Normalized `documents` table with metadata: symbol, type, language, source, URL, publication date.
- [ ] Document ingestion pipeline: extract → clean → chunk → embed → pgvector.
- [ ] Chunk size 800–1200 tokens with 100–200 overlap; tables handled specially.
- [ ] Retrieval endpoint ranks chunks and returns source citations.
- [ ] UI document search page shows ranked results with title, source, and date.
- [ ] Arabic queries retrieve Arabic documents; English queries retrieve English documents where available.

**Exit artifact:** Signed-off RAG phase checklist and sample query results.

---

## Milestone 4 — AI Investment Assistant

**Goal:** The assistant provides structured, cited, decision-support analysis for stocks and portfolios.

**User outcome:** A user clicks "Analyze with AI" and sees a recommendation, confidence score, reasons, risks, missing data, and data timestamp in Arabic or English.

**Depends on:** Implementation Guide Phases 7–10 and Phase 9 Stage B.

**Acceptance criteria:**

- [ ] `LLMProvider` abstraction with `OllamaLLMProvider`.
- [ ] Tool-calling layer exposes portfolio, market, financial, technical, risk, and RAG tools.
- [ ] `PortfolioAnalysisResponse` schema enforced; no free-form text as primary output.
- [ ] Single-stock and whole-portfolio analysis endpoints return structured results.
- [ ] Risk engine integrated; breaches surface in analysis.
- [ ] AI analysis card in dashboard shows recommendation, confidence /100, sources, `data_as_of`.
- [ ] Forbidden-phrase guard prevents guaranteed-return or probability claims.

**Exit artifact:** Signed-off Phase 07 and Phase 08 exit-gate checklists.

---

## Milestone 5 — Conversational AI Chat

**Goal:** Users can have a natural-language conversation about their portfolio and stocks.

**User outcome:** A user types "حلل محفظتي بالكامل" in chat, sees tool calls, and receives a cited Arabic answer.

**Depends on:** Implementation Guide Phase 12.

**Acceptance criteria:**

- [ ] Chat sessions and messages persisted in PostgreSQL.
- [ ] SSE endpoint streams tool calls, tool results, and answer tokens.
- [ ] Arabic and English responses localized; RTL layout for Arabic.
- [ ] Intent routing selects appropriate tools.
- [ ] Trade-execution requests are refused with a decision-support disclaimer.
- [ ] Every answer that uses tools includes citations and `data_as_of`.

**Exit artifact:** Signed-off Phase 10 exit-gate checklist.

---

## Milestone 6 — Backtesting and AI Evaluation

**Goal:** Recommendations are evaluated against historical data to detect look-ahead bias and hallucination.

**User outcome:** Internal reviewers can run backtests and an evaluation dataset; the system reports pass rates, returns, drawdowns, and failure categories.

**Depends on:** Implementation Guide Phases 15–16.

**Acceptance criteria:**

- [ ] Backtest engine runs on historical data with `as_of` cutoff.
- [ ] Look-ahead bias test passes (no future data leaks).
- [ ] Multiple scenarios produce stored CSV/JSON reports.
- [ ] AI evaluation harness runs a fixed question set in Arabic and English.
- [ ] Evaluation criteria cover numerical accuracy, tool usage, source correctness, no hallucination, reasoning quality, Arabic quality, timestamps, and safety.
- [ ] Baseline evaluation report saved; top failure categories triaged.
- [ ] At least one optimization cycle completed without reducing pass rate.

**Exit artifact:** Signed-off Phase 11 exit-gate checklist and baseline evaluation report.

---

## Milestone 7 — Release Readiness (Final Milestone)

**Goal:** The application is safe, documented, performant, and deployable for local personal use.

**User outcome:** A user can install the application locally and use it as a decision-support tool with clear disclaimers.

**Depends on:** All previous milestones.

**Acceptance criteria:**

- [ ] Investment, data-freshness, AI-limitation, and privacy disclaimers displayed and acknowledged.
- [ ] README and user guide in English and Arabic.
- [ ] Local setup guide verified on a clean machine.
- [ ] `.env.example` complete; no secrets committed.
- [ ] Performance validated on target hardware (16 GB RAM, RTX 3060 Laptop).
- [ ] Final test suite passes with no release-blocking failures.
- [ ] Security review and RTL review signed off.
- [ ] Docker Compose or start script runs from a fresh clone.
- [ ] Release notes written and version tag created (`v0.1.0`).

**Exit artifact:** Signed-off `docs/checklists/release-checklist.md` and git tag.

---

## Milestone Mapping Summary

| Milestone | Implementation Guide Phases | Deliverable user value |
|-----------|----------------------------|------------------------|
| 0 | Phase 0 | Local environment ready. |
| 1 | Phases 1–5 + Phase 9 Stage A | Add transactions, view correct P&L. |
| 2 | Phases 2–4 + Phase 9 Stage B stock page | See reliable stock snapshot. |
| 3 | Phases 5–6 | Ask questions about company reports. |
| 4 | Phases 7–10 + Phase 9 Stage B analysis/risk | Get structured AI analysis with citations. |
| 5 | Phase 12 | Have a natural-language assistant conversation. |
| 6 | Phases 15–16 | Trust recommendations through backtesting/evaluation. |
| 7 | Phase 12 Release Readiness | Install and use locally with safety disclaimers. |

---

## Milestone Dependency Graph

```text
Milestone 0 (Environment)
         │
         ▼
Milestone 1 (Portfolio Engine + Thin UI)
         │
         ├──────────────────────────────┐
         ▼                              ▼
Milestone 2 (Market/Financial/Technical)  Milestone 3 (Documents/RAG)
         │                              │
         └──────────────┬───────────────┘
                        ▼
              Milestone 4 (AI Assistant)
                        │
                        ▼
              Milestone 5 (AI Chat)
                        │
                        ▼
              Milestone 6 (Backtesting/Evaluation)
                        │
                        ▼
              Milestone 7 (Release Readiness)
```

---

## Notes

- Milestones are intentionally outcome-oriented, not code-oriented. A milestone is complete when the user value is demonstrable and the exit artifact is signed off.
- Phases 7, 8, 9, 10, 11, and 12 in the implementation guide map to milestones 4–7 and are covered in detail in `docs/phases/`.
- Future enhancements listed in the implementation guide (e.g., mobile app, cloud deployment, Arabic voice interface) are out of scope for these milestones and must be planned separately.
