# Scratchpad

## Lessons / Gotchas

- Frontend API base URL (`NEXT_PUBLIC_API_BASE_URL`) must be used in the browser too; returning `/api` from `getApiBaseUrl()` only works if Next.js rewrites are configured for every backend route. When routers use mixed prefixes (`/portfolio` vs `/api/settings`, `/api/risk`), direct calls with the full backend URL plus the correct path are simpler. Add `CORSMiddleware` to FastAPI so the dev frontend on a different port can call the backend directly.
- Risk/router endpoints created with `APIRouter(prefix="/api/...")` need frontend paths prefixed with `/api/...` when calling directly; portfolio endpoints remain `/portfolio/...`.

## Task: Implement Phase 08 — Risk Engine

- Implemented Phase 08 core:
  - [x] `RiskLimits`, `RiskReport`, `RiskBreach`, `RebalancingSuggestion` schemas with bilingual fields.
  - [x] `risk_limits` PostgreSQL table and migration `0007_risk_limits`; GET/POST `/api/settings/risk-limits` endpoints.
  - [x] Deterministic `backend/app/services/risk_engine.py` implementing position concentration, sector allocation, cash percentage, portfolio volatility, max drawdown, correlation matrix, beta, Sharpe ratio using pure Python (no pandas).
  - [x] `RiskReport` generation with breach detection for `MAX_SINGLE_POSITION`, `MAX_SECTOR_EXPOSURE`, `MIN_CASH`, and optional `MAX_PORTFOLIO_VOLATILITY`.
  - [x] Risk REST endpoints: `GET /api/risk/portfolio`, `/api/risk/portfolio/summary`, `/api/risk/portfolio/rebalancing`.
  - [x] Integrated risk report into Phase 7 AI analysis orchestrator (`portfolio_ai.py`) so `portfolio_assessment` reflects concentration/overweight and Arabic warnings are emitted on critical breaches.
  - [x] Added Arabic risk labels (`frontend/lib/labels/ar-risk.json`) and tests.
  - [x] Backend tests for pure risk functions and integration tests for risk endpoints.
  - [x] `make test`, `make test-integration`, `make lint`, `make typecheck` all pass.
- Remaining future work: benchmark series for beta, richer correlation visualization, EGP T-bill risk-free rate source, and Arabic golden evaluation for risk prose.

## Task: Implement Phase 09 — Next.js Dashboard (Stage A)

- Implemented Stage A thin portfolio UI and foundation:
  - [x] Locale/RTL foundation already present; extended with new navigation keys and Arabic translations for Settings, Risk, Dashboard, Analysis, Documents, Stocks, Delete, Save, Breaches, etc.
  - [x] New pages: `/` dashboard hub with links, `/settings` to view/edit risk limits, `/risk` to view risk summary and breaches, `/analysis` placeholder.
  - [x] API wrappers in `frontend/lib/api.ts` for risk limits, risk report, rebalancing, analysis, and transaction deletion.
  - [x] Added `PUT /portfolio/transactions/{id}` and `DELETE /portfolio/transactions/{id}` backend endpoints plus service functions.
  - [x] Added Delete button to the portfolio transactions table.
  - [x] Fixed frontend/backend routing: added FastAPI `CORSMiddleware`, made `getApiBaseUrl()` use `NEXT_PUBLIC_API_BASE_URL` in the browser, and used `/api/settings/*`, `/api/risk/*`, `/api/analysis/*` paths in the frontend API wrappers.
  - [x] All frontend lint, typecheck, and unit tests pass.
- Remaining future work: Stage B full pages (stock screener, stock detail charts, AI analysis cards, documents search), Playwright E2E tests, and charting library integration.

## Task: Implement Phase 07 — Portfolio AI

- Implemented Phase 07 core:
  - [x] `PortfolioAnalysisResponse`/`WholePortfolioAnalysis` Pydantic schemas with enums for recommendation, assessments, bilingual reasons/risks/missing info, citations, and `data_as_of`.
  - [x] `ai_analysis_logs` PostgreSQL table and model for audit/debugging with prompt/model/version, durations, and status.
  - [x] Deterministic analysis assembler in `backend/app/services/portfolio_ai.py`:
    - Gathers quote, financial snapshot, technical indicators, historical prices, documents, news, and portfolio position/allocation.
    - Computes valuation, fundamental, technical, and portfolio assessments from verified metrics.
    - Falls back to deterministic structured output when LLM JSON is unavailable/malformed; still attempts LLM first for prose generation.
    - Enforces data freshness warnings and confidence caps.
  - [x] Guardrails: post-processor rejects forbidden phrases (guaranteed returns, probability claims, Arabic equivalents) and refuses trade execution.
  - [x] `POST /api/analysis/stock/{symbol}` and `POST /api/analysis/portfolio` endpoints; 422 for unknown symbol, 503 on unexpected AI errors.
  - [x] Versioned system prompt at `docs/prompts/portfolio-analysis-v1.md`.
  - [x] Arabic/RTL frontend labels file `frontend/lib/labels/ar.json` and unit test.
  - [x] Backend tests: schema validation, forbidden-phrase detection, structured stock/portfolio responses, Arabic reasons, unknown-symbol handling.
  - [x] `make test`, `make test-integration`, `make lint`, `make typecheck` all pass.
- Remaining future work: full Arabic golden evaluation dataset, richer LLM-driven prose with deterministic metric validation, screenshot/Storybook RTL card, and local Ollama integration tests on target hardware.

## Task: Implement Phase 06 — Ollama and Tools

- Implemented Phase 06 core:
  - [x] `LLMProvider` protocol plus `FakeLLMProvider` (deterministic queued responses) and `OllamaLLMProvider` (local `/api/chat` with tool support, bounded timeout, model/version tracking).
  - [x] Typed message/tool-call/result/response schemas in `backend/app/ai/schemas.py`.
  - [x] Tool registry in `backend/app/tools/` with Pydantic argument schemas, JSON-schema export, and read-only allowlist.
  - [x] Initial tools wrapping Phases 01–05 domain services:
    - `get_portfolio`, `get_position`, `get_quote`, `get_historical_prices`, `get_financial_snapshot`, `get_technical_indicators`, `search_documents`, `get_latest_news`, `calculate_portfolio_allocation`, `calculate_sector_allocation`.
  - [x] Orchestrator with system safety prompt, budgeted tool-call loop, validation, deduplication, source/warning collection, and policy checks (no trade execution, no guaranteed returns, resist prompt injection).
  - [x] `POST /api/ai/analyze` endpoint with structured response: interpretation, verified_facts, calculated_metrics, retrieved_information, assumptions, missing_information, warnings, data_as_of, sources, model, tool_calls, language.
  - [x] Tests: fake provider contract, tool-call execution, Arabic language detection, unknown-tool rejection, and endpoint structure.
  - [x] `make test`, `make test-integration`, `make lint`, `make typecheck` all pass.
- Remaining future work: full Arabic evaluation set, Ollama integration tests on target hardware, conversation persistence, prompt/tool version manifest, and richer citation validation/repair.

## Task: Implement Phase 05 — Documents and RAG

- Implemented Phase 05 core:
  - [x] Added `pgvector==0.4.1` and created `documents` + `document_chunks` tables with a `vector(2560)` column matching Qwen3-Embedding-4B dimensions.
  - [x] `Document` and `DocumentChunk` models preserve source URL, publication date, language, checksum, version, page/section lineage, and indexed status.
  - [x] Deterministic `FakeEmbeddingProvider` for offline tests; `OllamaEmbeddingProvider` for local Qwen embeddings with dimension validation.
  - [x] Word-based chunker with configurable target/overlap, heading preservation, and a table-aware atomic heuristic.
  - [x] Idempotent ingestion service that hashes content, chunks, embeds, and stores chunks atomically.
  - [x] Vector search service with metadata pre-filters (symbol, document type, language, `as_of` publication cutoff), cosine ranking, deduplication, and citation metadata.
  - [x] API routes: `POST /api/documents`, `GET /api/documents`, `POST /api/documents/search`.
  - [x] Unit tests for chunking/embeddings and integration tests for ingestion, listing, search, and `as_of` filtering.
  - [x] `make test`, `make test-integration`, `make lint`, `make typecheck` all pass.
- Remaining future work: richer PDF/HTML extraction, OCR deferral, source-allowlist validation, public-source collection policy doc, tokenizer-based chunking, dedicated vector indexes (IVFFlat/HNSW), re-indexing jobs, and bilingual golden retrieval evaluation dataset.

## Task: Implement Phase 04 — Technical Analysis

- Implemented Phase 04 core:
  - [x] Deterministic pure functions for SMA 20/50/200, Wilder RSI 14, EMA, and MACD (12/26/9) in `backend/app/domain/technical.py`.
  - [x] Input normalization: ascending sort, duplicate detection, OHLC invariants, finite values.
  - [x] Deterministic 252-bar COMI OHLCV fixture generated into `backend/app/providers/market/fixtures/mock_quotes.json` under a new `history` key.
  - [x] `MockMarketDataProvider` updated to use `history` when available and fall back to `bars`.
  - [x] Snapshot service/assembler and `GET /api/stocks/{symbol}/technical?as_of=&interval=1d` route.
  - [x] Response includes symbol, interval, last timestamp, observation count, parameters, indicators, latest volume, source, freshness, and warnings.
  - [x] Golden unit tests for indicators and integration tests for complete snapshot, unknown stock, unsupported interval, and insufficient history.
  - [x] `make test`, `make test-integration`, `make lint`, `make typecheck` all pass.
- Remaining future work: Bollinger Bands, ATR, volume indicators, support/resistance, exchange-calendar gap detection, and public-source cross-validation.

## Task: Implement Phase 03 — Financial Engine

- Implemented Phase 03 core:
  - [x] `FinancialStatement` model with provenance fields (period, scope, currency, unit_scale, source, version).
  - [x] Migration `0004_financial_statements.py`.
  - [x] Pure Decimal ratio functions: P/E, P/B, ROE, ROA, liabilities-to-equity, profit margin, growth, dividend yield with null/zero/negative safeguards.
  - [x] Deterministic mock financial-data provider and COMI fixtures with two annual periods.
  - [x] Repository with idempotent upsert, latest-statement selector respecting `published_at`, and prior-period selector for growth.
  - [x] Snapshot assembler that combines the latest statement with the Phase 02 quote, exposes source lineage, and emits warnings instead of inventing values.
  - [x] API route `GET /api/stocks/{symbol}/financials/snapshot?as_of=`.
  - [x] Golden unit tests for ratios and integration tests for snapshot, unknown stock, and `as_of` look-ahead.
  - [x] `make test`, `make test-integration`, `make lint`, `make typecheck` all pass.
- Phase 03 is functionally complete. Remaining refinements (future): Arabic/English ingestion round-trip, public-source ingestion adapter beyond mocks, deeper restatement version tests.

## Task: Implement Phase 02 — Market Data

- Started by fixing the Phase 01 Arabic number-formatting bug in `frontend/lib/format.ts` (added `numberingSystem: "arab"` for `ar` locale) so Phase 01 acceptance is now clean.
- Phase 02 progress:
  - [x] Provider protocol + DTOs (`Quote`, `Bar`, `Volume`) and typed errors in `backend/app/providers/market_data.py`.
  - [x] Deterministic mock provider with `get_quote`, `get_historical_prices`, and `get_volume`; OHLCV fixture data added.
  - [x] `stock_prices` table migration (`0003_stock_prices.py`) and `StockPrice` model.
  - [x] Idempotent `upsert_bars` repository in `backend/app/repositories/market_data.py`.
  - [x] Quote/history/volume routes: `GET /api/stocks/{symbol}/quote`, `/api/stocks/{symbol}/history`, `/api/stocks/{symbol}/volume`.
  - [x] Tests: provider contract unit tests + integration tests for the new routes.
  - [x] `make test`, `make test-integration`, `make lint`, and `make typecheck` all pass.
- Completed Phase 02 closure items:
  - [x] Implemented a real web adapter `OanorProvider` in `backend/app/providers/market/oanor.py` for the Oanor EGX API (quote/volume) and Oanor Finance API (history), gated by `MARKET_DATA_PROVIDER=oanor` and `OANOR_API_KEY`.
  - [x] Added public-source validation notes and selection matrix to `docs/08-data-providers.md`. Recommendation: Oanor EGX API is the best available documented source, but it is upstreamed from TradingView, whose terms restrict non-display/machine-driven use, so it remains opt-in / not production-ready until legal review and a sample cross-check.
  - [x] Added bounded HTTP timeouts, typed errors, and mocked HTTP tests for the real adapter.
- Remaining future work (not required for Phase 02 acceptance):
  - Session-aware freshness (trading hours/holidays) and richer fault-injection tests for upstream failures.
  - Optional: expose market-data endpoints in the frontend UI.
  - Optional: validate and wire a different real source if Oanor/TradingView terms are unsuitable.

## Task: Run the EGX AI Portfolio Manager app

- [x] Install dependencies (`make install PYTHON=/opt/homebrew/bin/python3`)
- [x] Start Docker Desktop (it was not running)
- [x] Start PostgreSQL container (`make db-up`)
- [x] Run Alembic migrations (`make migrate`)
- [x] Start FastAPI backend (`make backend`)
- [x] Start Next.js frontend (`make frontend`)

## Lessons

- This project's Makefile hardcodes `PYTHON := $(HOME)/.pyenv/versions/3.11.11/bin/python`. If pyenv 3.11.11 is not installed, override it on the command line: `make <target> PYTHON=/opt/homebrew/bin/python3` (or the local Python 3.11+ path).
- A local Postgres was already listening on port 5432, so I had to change `POSTGRES_PORT` and `DATABASE_URL` in `.env` to 5433 before `make db-up` could succeed.
- `get_session()` yields a SQLAlchemy session but does **not** auto-commit; write endpoints must call `session.commit()` explicitly, or subsequent requests will not see the data.
