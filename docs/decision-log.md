# Decision Log

This document records significant architectural, product, and engineering decisions made during the EGX AI Portfolio Manager project. Each entry includes the decision, context, alternatives considered, consequences, and the date/owner. Decisions here are derived from the Implementation Guide and the implementation-ready phase plans.

---

## Entry 001 — Local-First, Decision-Support Scope

| Field | Value |
|-------|-------|
| **Date** | 2026-09-02 |
| **Owner** | Project lead / AI safety reviewer |
| **Status** | Accepted |
| **Decision** | The first release is a local-first, decision-support assistant. It does not execute trades automatically and does not provide personalized investment advice. |
| **Context** | The project targets personal investment research on the Egyptian Stock Exchange. Automated trading carries regulatory, financial, and safety risks beyond the initial scope. |
| **Alternatives considered** | 1. Semi-automated trade execution (rejected: regulatory and liability risk). 2. Cloud-hosted SaaS (rejected: local-first keeps portfolio data private and reduces infrastructure cost). 3. Pure static dashboard without AI (rejected: does not meet the assistant goal). |
| **Consequences** | All phases must include a "no auto-trading" guardrail. Every AI output must include a decision-support disclaimer. The UI must not contain buy/sell order buttons connected to a broker. |
| **Related phases** | All phases; explicit in Phase 07, 10, 12. |

---

## Entry 002 — Local LLM: Qwen3.5 9B on Ollama

| Field | Value |
|-------|-------|
| **Date** | 2026-09-02 |
| **Owner** | ML / inference lead |
| **Status** | Accepted |
| **Decision** | Use `ollama pull qwen3.5:9b` as the reasoning model. Do not start with 27B/35B/70B models. |
| **Context** | Target hardware is 16 GB RAM, Intel i7-11800H, RTX 3060 Laptop 6 GB VRAM. Larger models exceed comfortable local inference limits and would force cloud usage. |
| **Alternatives considered** | 1. Qwen3 14B/32B (rejected: slower, more VRAM). 2. External OpenAI/Claude API (rejected: recurring cost, data leaving local machine, EGX data privacy concerns). 3. Smaller 3B/4B model (rejected: weaker Arabic reasoning and tool calling). |
| **Consequences** | All prompts and tools must be optimized for Qwen3.5 9B. Evaluation harness must be run on this exact model. Larger models can be evaluated later when hardware is upgraded. |
| **Related phases** | Phase 00 (Environment), Phase 07 (Portfolio AI), Phase 10 (AI Chat), Phase 12 (Release). |

---

## Entry 003 — Separate Embedding Model: Qwen3-Embedding 4B Q4

| Field | Value |
|-------|-------|
| **Date** | 2026-09-02 |
| **Owner** | ML / RAG lead |
| **Status** | Accepted |
| **Decision** | Use `ollama pull qwen3-embedding:4b-q4_K_M` for document embeddings. Keep embeddings separate from reasoning model. |
| **Context** | Reasoning and embedding are different tasks. A dedicated embedding model improves RAG quality and allows independent scaling/upgrades. |
| **Alternatives considered** | 1. Use the same Qwen3.5 9B model for embeddings (rejected: inefficient, larger context, worse retrieval). 2. Use a non-Arabic embedding model (rejected: poor Arabic document retrieval). |
| **Consequences** | RAG pipeline must specify the embedding model explicitly. Document chunking and retrieval tests must be evaluated with this model. |
| **Related phases** | Phase 06 (RAG), Phase 10 (AI Chat). |

---

## Entry 004 — LLM Is Not Source of Truth for Numerical Data

| Field | Value |
|-------|-------|
| **Date** | 2026-09-02 |
| **Owner** | Engineering lead / AI safety reviewer |
| **Status** | Accepted |
| **Decision** | All prices, ratios, P&L, allocations, technical indicators, and portfolio values must come from deterministic application code. The LLM receives only calculated/retrieved facts and performs reasoning over them. |
| **Context** | LLMs hallucinate numbers. Financial decisions require reproducible, auditable calculations. |
| **Alternatives considered** | 1. Let the LLM compute ratios from raw text (rejected: unreliable). 2. Let the LLM estimate prices or returns (rejected: dangerous for decision support). |
| **Consequences** | Every number in AI output must be traceable to a tool result or deterministic calculation. Post-processor validates numeric claims. Unit tests cover all calculations. |
| **Related phases** | Phase 01 (Portfolio Engine), Phase 02 (Market Data), Phase 03 (Financial Data), Phase 04 (Technical Analysis), Phase 07 (Portfolio AI), Phase 08 (Risk Engine). |

---

## Entry 005 — PostgreSQL + pgvector as RAG Store

| Field | Value |
|-------|-------|
| **Date** | 2026-09-02 |
| **Owner** | Data / backend lead |
| **Status** | Accepted |
| **Decision** | Use PostgreSQL with the pgvector extension for document embeddings and vector search. |
| **Context** | The team already uses PostgreSQL for transactional data. Adding a separate vector database increases operational complexity. |
| **Alternatives considered** | 1. ChromaDB (rejected: extra service, less mature). 2. FAISS in memory (rejected: not persistent, harder to scale). 3. Weaviate/Pinecone (rejected: external service, cost). |
| **Consequences** | Document chunks share the same database as portfolio and market data. Backup and migration processes must account for embedding columns. Vector indexes must be configured. |
| **Related phases** | Phase 00 (Environment), Phase 06 (RAG), Phase 10 (AI Chat). |

---

## Entry 006 — Market Data Provider Abstraction

| Field | Value |
|-------|-------|
| **Date** | 2026-09-02 |
| **Owner** | Backend lead |
| **Status** | Accepted |
| **Decision** | Build a `MarketDataProvider` abstraction with `EGXProvider` and `MockMarketDataProvider`. All application code depends on the abstraction, not a specific source. |
| **Context** | EGX data sources may change, require credentials, or be unavailable in development. A mock provider enables deterministic tests and offline work. |
| **Alternatives considered** | 1. Direct EGX API calls everywhere (rejected: brittle, hard to test). 2. Only use free Yahoo Finance (rejected: EGX coverage may be incomplete). |
| **Consequences** | Every market data consumer uses `MarketDataProvider.get_quote()` and `get_historical_prices()`. CI runs against `MockMarketDataProvider`. Real EGX provider is tested manually. |
| **Related phases** | Phase 02 (Market Data), Phase 04 (Technical Analysis), Phase 08 (Risk Engine), Phase 11 (Backtesting). |

---

## Entry 007 — Thin Portfolio UI Before Full Dashboard

| Field | Value |
|-------|-------|
| **Date** | 2026-09-02 |
| **Owner** | Frontend / product lead |
| **Status** | Accepted |
| **Decision** | Build a thin, data-first portfolio UI (transaction CRUD, holdings, simple sector allocation) before adding charts, AI cards, and advanced pages. |
| **Context** | Portfolio calculations are the foundation. If the thin UI cannot correctly add a transaction and show P&L, adding dashboards and AI will mask the bug. The first milestone in the guide is exactly this thin portfolio flow. |
| **Alternatives considered** | 1. Build full dashboard first (rejected: brittle, harder to debug calculation errors). 2. Build stock pages before portfolio (rejected: portfolio is the core user value and the first milestone). |
| **Consequences** | Phase 09 is split into Stage A (thin portfolio UI) and Stage B (full dashboard). Stage A must be signed off before Stage B begins. This is documented in `docs/phases/09-dashboard.md`. |
| **Related phases** | Phase 09 (Dashboard), Phase 01 (Portfolio Engine). |

---

## Entry 008 — Configurable Risk Limits, Not Hard-Coded

| Field | Value |
|-------|-------|
| **Date** | 2026-09-02 |
| **Owner** | Risk / backend lead |
| **Status** | Accepted |
| **Decision** | Store portfolio risk limits (`max_single_position`, `max_sector_exposure`, `min_cash`, etc.) in configuration that can be changed without code redeployment. The LLM cannot modify these limits. |
| **Context** | Risk tolerance is personal. The AI must explain breaches against limits the user owns, not invent its own thresholds. |
| **Alternatives considered** | 1. Hard-coded limits (rejected: inflexible, hard to audit). 2. Let the LLM suggest and set limits (rejected: safety risk, non-deterministic). |
| **Consequences** | Settings API exposes risk limits. Risk engine and AI analysis read limits from config. Changes are logged and immediately reflected. |
| **Related phases** | Phase 08 (Risk Engine), Phase 07 (Portfolio AI), Phase 09 (Dashboard). |

---

## Entry 009 — Structured AI Response Schema with Arabic Fields

| Field | Value |
|-------|-------|
| **Date** | 2026-09-02 |
| **Owner** | AI / backend lead |
| **Status** | Accepted |
| **Decision** | AI analysis output must conform to a strict Pydantic schema (`PortfolioAnalysisResponse`) that includes `reasons_ar`, `risks_ar`, `missing_information_ar`, and source citations. Free-form text is not the primary artifact. |
| **Context** | Structured output enables validation, citations, and consistent UI rendering. Arabic fields are required for RTL UX without on-the-fly translation. |
| **Alternatives considered** | 1. Free-form LLM text in UI (rejected: impossible to validate or cite). 2. Translate English output to Arabic at runtime (rejected: loses nuance, adds latency, inconsistent financial terminology). |
| **Consequences** | LLM prompt must request structured JSON. Frontend renders fields directly. Validation tests enforce schema completeness. |
| **Related phases** | Phase 07 (Portfolio AI), Phase 09 (Dashboard), Phase 10 (AI Chat). |

---

## Entry 010 — Confidence Score Is Not a Probability

| Field | Value |
|-------|-------|
| **Date** | 2026-09-02 |
| **Owner** | AI safety / product lead |
| **Status** | Accepted |
| **Decision** | Display AI confidence as "72/100" or "Confidence: 72/100". Never present it as "72% probability that the stock will rise." |
| **Context** | LLM confidence is not calibrated probability. Presenting it as a probability misleads users into believing guaranteed outcomes. |
| **Alternatives considered** | 1. Show probability percentage (rejected: misleading). 2. Hide confidence entirely (rejected: users need a sense of model certainty). |
| **Consequences** | UI label map and system prompt both enforce this language. Forbidden-phrase guard flags probability-of-return claims. |
| **Related phases** | Phase 07 (Portfolio AI), Phase 10 (AI Chat), Phase 12 (Release). |

---

## Entry 011 — Backtesting with Strict `as_of` Cutoff

| Field | Value |
|-------|-------|
| **Date** | 2026-09-02 |
| **Owner** | Quant / backend lead |
| **Status** | Accepted |
| **Decision** | Every backtest must pass an explicit `as_of` date to all data queries. Future prices, documents, and news are strictly excluded. |
| **Context** | Look-ahead bias destroys the validity of backtests and evaluation. The AI must be tested only on information available at the simulated time. |
| **Alternatives considered** | 1. Use "latest" data by default and manually filter (rejected: error-prone). 2. Trust the LLM not to use future data (rejected: LLM has no inherent time concept without explicit filtering). |
| **Consequences** | All providers and retrieval functions accept `as_of`. Backtest engine logs cutoffs. A dedicated test asserts no future data leakage. |
| **Related phases** | Phase 11 (Backtesting and Evaluation). |

---

## Entry 012 — RTL-First Arabic UX

| Field | Value |
|-------|-------|
| **Date** | 2026-09-02 |
| **Owner** | Frontend / UX lead |
| **Status** | Accepted |
| **Decision** | Arabic locale is a first-class citizen. The UI must support RTL layout, Arabic numerals/currency formatting, EGP currency prefix (`ج.م`), and `DD/MM/YYYY` dates. English locale remains LTR with `EGP` and `YYYY-MM-DD`. |
| **Context** | Primary users are likely Arabic-speaking Egyptian investors. Poor RTL support degrades trust. English support is required for mixed-language users. |
| **Alternatives considered** | 1. English-only UI with Arabic content translated at runtime (rejected: bad UX, wrong numerals/currency). 2. Auto-detect Arabic text and flip only message bubbles (rejected: inconsistent with a global locale system). |
| **Consequences** | Locale middleware sets `dir` and `lang` on `<html>`. All numeric/date formatting uses `Intl.NumberFormat` / `Intl.DateTimeFormat` with `ar-EG`. Every page must pass RTL visual regression. |
| **Related phases** | Phase 09 (Dashboard), Phase 10 (AI Chat), Phase 12 (Release). |

---

## Entry 013 — No Automatic Trade Execution

| Field | Value |
|-------|-------|
| **Date** | 2026-09-02 |
| **Owner** | Product / compliance lead |
| **Status** | Accepted |
| **Decision** | The application must not contain any endpoint, tool, or UI control that can automatically place a buy or sell order with a broker. Rebalancing suggestions are read-only. |
| **Context** | Automated trading requires broker integration, regulatory approval, and extensive safety controls. The first release is decision-support only. |
| **Alternatives considered** | 1. Build a simulated paper-trading endpoint (rejected: out of scope for v0.1.0, could be added later). 2. Allow one-click order draft for manual submission (rejected: still too close to execution; defer). |
| **Consequences** | No `POST /api/orders` exists. Rebalancing suggestions display `delta_shares_estimate` as informational only. Chat refuses trade-execution requests. |
| **Related phases** | Phase 07 (Portfolio AI), Phase 08 (Risk Engine), Phase 10 (AI Chat), Phase 12 (Release). |

---

## Entry 014 — Evaluation Harness Gates Releases

| Field | Value |
|-------|-------|
| **Date** | 2026-09-02 |
| **Owner** | AI / QA lead |
| **Status** | Accepted |
| **Decision** | The AI evaluation harness pass rate and backtest results must be reviewed before each release. A drop in pass rate blocks release until triaged. |
| **Context** | Without an evaluation gate, prompt or model changes can silently degrade accuracy, hallucination, or Arabic quality. |
| **Alternatives considered** | 1. Release based on manual spot checks (rejected: not reproducible). 2. Block release on 100% pass rate (rejected: unrealistic for v0.1.0; ≥80% target with triage). |
| **Consequences** | `eval-reports/` stores baseline and iteration reports. Release checklist includes evaluation result review. Known failures are documented as limitations if not blocking. |
| **Related phases** | Phase 11 (Backtesting and Evaluation), Phase 12 (Release Readiness). |

---

## How to Add a New Decision

When a new significant decision is made during implementation:

1. Copy the table template above.
2. Assign the next sequential entry number.
3. Record date, owner, status, decision, context, alternatives, consequences, and related phases.
4. Update any phase documentation affected by the decision.
5. If the decision reverses an earlier entry, mark the old entry as `Superseded` and link to the new entry.
