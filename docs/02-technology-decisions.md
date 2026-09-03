# Technology Decisions

## Decision policy

The project favors mature, locally operable, well-tested components and the smallest architecture that satisfies the [scope](00-product-scope.md). Versions below express the approved baseline and pinning policy; because this is a documentation-only repository, bootstrap work must verify and lock exact compatible patch versions in manifests/lockfiles rather than copy an unverified “latest” number.

Use currently supported stable releases at bootstrap, record the resolved versions, and upgrade deliberately with tests and migration notes. Avoid prerelease software for financial calculations or persistence.

## Decision summary

| Area | Decision | Version/pinning guidance | Why |
|---|---|---|---|
| Runtime | Python | CPython 3.11+; target one supported minor and exact lock | Guide minimum, broad scientific/AI compatibility. |
| API | FastAPI + Uvicorn | Compatible stable releases, exact lock | Typed async-capable API and OpenAPI generation. |
| Validation | Pydantic v2 | Same lock as backend | Strong boundary schemas and settings ecosystem. |
| ORM | SQLAlchemy 2.x | Exact lock | Explicit unit-of-work/data mapping without coupling domain to ORM. |
| Migrations | Alembic | Exact lock | Reproducible, reviewable PostgreSQL schema evolution. |
| Backend packages | `uv` | Pin `uv`; commit `uv.lock` | Fast reproducible Python environments and a single workflow. |
| Data/calculation | Pandas plus focused pure functions | Exact locks | Tabular ingestion/series analysis; domain accounting remains explicit and testable. |
| Technical analysis | `pandas-ta` initially, accepted only after benchmark spike | Exact commit/release if chosen | Easier local setup than native TA-Lib; calculations must be verified against golden fixtures. |
| Frontend | Next.js + React + TypeScript | Supported stable Next.js line; exact package lock; TypeScript strict mode | App routing, local UI, typed contracts, and mature i18n/accessibility ecosystem. |
| Frontend packages | `pnpm` via Corepack | Pin package-manager version; commit `pnpm-lock.yaml` | Efficient deterministic installs. |
| Database | PostgreSQL | Supported stable major selected at bootstrap and fixed in Compose | ACID ledger storage, robust decimals/time, full-text/JSON capabilities. |
| Vector search | pgvector | Version compatible with selected PostgreSQL image; pin image/digest | Keeps transactional metadata and vectors together; avoids another service. |
| LLM runtime | Ollama | Pin/document tested local version | Simple local NVIDIA-capable model API. |
| Reasoning model | `qwen3.5:9b` | Record immutable model digest, parameters, and prompt version | Fits target hardware better than 27B+ options and supports Arabic/English/tool use. |
| Embeddings | `qwen3-embedding:4b-q4_K_M` | Record model digest and vector dimension before migration | Separate local semantic model suitable for bounded hardware. |
| RAG orchestration | LlamaIndex, used narrowly | Exact lock | Document/node/retrieval primitives with metadata filtering; business/tool orchestration stays application-owned. |
| Charts | TradingView Lightweight Charts | Exact npm lock | Efficient financial time-series rendering. |
| Backend testing | Pytest | Exact lock with needed plugins | Fixtures, parametrization, integration markers, and financial golden tests. |
| Frontend unit/component | Vitest + Testing Library | Exact lock | Fast TypeScript tests focused on user-visible behavior. |
| End-to-end | Playwright | Pin package and browser artifacts | Real browser coverage for RTL/LTR, accessibility, errors, and critical flows. |
| Local orchestration | Docker Compose | Compose v2; pin service images | Reproducible PostgreSQL/pgvector and optional app services without production complexity. |

## Backend decisions

### Python, FastAPI, and Pydantic

Python owns financial calculations, ingestion, retrieval, and orchestration. FastAPI provides transport only; core modules must remain framework-independent. Pydantic request/response models validate external boundaries, and generated OpenAPI is the contract source for frontend client generation/checking.

Use `Decimal` for money, quantities, prices, ratios where precision policy demands it; never silently convert to `float` in portfolio accounting. Use timezone-aware `datetime`. Define strict enums for transaction/document/recommendation states.

**Alternative considered:** Django. It provides a mature integrated stack but adds conventions and UI/admin capabilities not required by this local API-first modular monolith. Revisit only if its admin/auth features become a concrete need.

### SQLAlchemy and Alembic

Keep SQLAlchemy persistence models and repositories in infrastructure modules; domain objects and calculations must not inherit ORM behavior. Alembic migrations are reviewed, reversible where practical, and tested from an empty database and the prior supported state. Production-like data must never be edited by ad hoc startup `create_all` behavior.

**Alternatives:** SQLModel reduces duplication but more tightly combines validation/persistence concerns; raw SQL remains appropriate for optimized pgvector or reporting queries behind repositories, not as the sole persistence architecture.

### Package and quality tooling

Use `uv` for environments, dependency resolution, locking, and command execution. At bootstrap, select a formatter/linter and type checker (recommended: Ruff plus mypy or Pyright) and document exact commands. This choice is intentionally finalized when the backend scaffold exists so configuration can be validated, but strict type checking and linting are required gates.

Pandas is suitable for ingestion and time series, not an excuse to hide ledger semantics in mutable data frames. Portfolio formulas should be small pure functions/services with golden cases. Evaluate `pandas-ta` against known SMA/RSI/MACD fixtures, including warm-up/null conventions; use TA-Lib only if benchmark accuracy or performance justifies native installation complexity.

## Frontend decisions

Use Next.js App Router, React, and strict TypeScript. Prefer server rendering for stable shell/reference content and client components only for interactive portfolio forms, charts, locale switching, and chat. The frontend consumes the API; no financial source-of-truth calculation is duplicated there.

Use standards-based internationalization and a small message-catalog library selected during bootstrap (for example, `next-intl`) only after confirming App Router support. Requirements are more important than library choice:

- route or persisted locale selection;
- top-level `lang` and `dir`;
- CSS logical properties;
- locale-neutral API numbers and locale-aware output;
- LTR isolation for symbols/formulas/URLs/timestamps;
- translated accessibility labels, errors, stale warnings, sources, and disclaimers;
- no chart-axis reversal that changes chronological meaning.

Do not adopt a large component system by default. Start with accessible semantic components and design tokens; add a library only after confirming keyboard, screen reader, mixed-script, and RTL behavior.

**Alternative considered:** a Python-rendered UI. It could reduce languages but is weaker for the planned interactive chart/chat experience and does not match the source guide.

## PostgreSQL and pgvector

One PostgreSQL instance stores the ledger, normalized research data, provenance, settings, documents, and vectors. Enable pgvector through a migration. Select a supported PostgreSQL major and compatible pgvector image during bootstrap; pin image tags and preferably digests. Backup and restore must include vectors and migration state.

Use `numeric` with deliberately selected precision/scale, `timestamptz`, foreign keys, checks, unique/idempotency constraints, and indexes based on query plans. Do not store canonical money as JSON or floating point. Vector dimension is fixed by the verified embedding model before creating the column.

**Alternative considered:** a dedicated vector database. Rejected for MVP because metadata, vectors, and transactions fit one local database. Revisit only with measured retrieval/scale limitations.

## Local AI and RAG

### Ollama and Qwen

Ollama runs locally and is accessed only through a backend `LLMProvider`/`EmbeddingProvider`. Reasoning and embedding models are independently configurable. Record model names, immutable digests, context/batch/concurrency settings, system prompt version, and generation parameters with evaluation results.

The hardware baseline rules out 27B/35B/70B defaults. Limit context, concurrent inference, and embedding batches. Model unavailability must not disable deterministic portfolio/research endpoints.

### LlamaIndex

Choose LlamaIndex for initial extraction/node/index/retrieval integration, but wrap it behind application interfaces. Do not let framework agents define authorization, financial tools, safety rules, or response schemas. Use direct pgvector queries where simpler.

**Alternative considered:** LangChain. It is viable, but choosing both increases abstraction and maintenance. Re-evaluate only if a documented capability is missing. A custom minimal pipeline remains preferable for portions where library behavior obscures metadata or point-in-time filtering.

Chunking starts at 800–1200 tokens with 100–200 overlap and is tuned using retrieval evaluations. Financial tables require structure-aware processing. Arabic extraction quality and cross-language retrieval must be measured, not assumed.

## Market-data technology decision

No public EGX website/API is approved merely by naming it. First implement a source-neutral provider and mock fixtures. A time-boxed validation spike must document:

1. access terms, licensing/redistribution constraints, robots policy, and whether automated access is permitted;
2. symbols, instruments, fields, historical depth, corporate actions, and market-calendar coverage;
3. EGP/currency semantics, timezone, observation/publication timestamp, quote delay, and session behavior;
4. rate limits, authentication, anti-bot controls, expected request volume, and caching permission;
5. availability and schema/parser stability over a representative observation period;
6. data-quality comparison against known samples;
7. retry/backoff, stale-cache, source-failure, fixture-sanitization, and replacement plan.

If no source passes, the MVP must use manual imports/fixtures and clearly state data limitations. Never bypass technical or legal access controls.

## Testing decisions

- **Pytest unit tests:** ledger, P&L, decimal/rounding, ratios, indicators, risk, freshness, and edge cases.
- **Provider contract tests:** one reusable suite for mock and every concrete provider; live tests are opt-in and never required for deterministic CI.
- **Integration tests:** real PostgreSQL/pgvector, migrations, repositories, retrieval, and mocked Ollama HTTP boundaries.
- **Vitest/Testing Library:** localized rendering, forms, states, bidirectional values, and API-client behavior.
- **Playwright:** milestone flows in Arabic/English, RTL/LTR, keyboard operation, source/freshness display, responsive layout, and failure states.
- **AI evaluations:** fixed bilingual dataset scoring numerical accuracy, correct tools, citations, missing evidence, no hallucination, reasoning, safety language, and Arabic quality.
- **Backtests:** point-in-time eligibility, reproducible model/input versions, fees/turnover, benchmark return, drawdown, win rate, and Sharpe; explicitly test against look-ahead leakage.

Coverage percentages alone are insufficient. Every financial branch and safety failure needs an asserted behavior. Pin timezone/clock and use sanitized deterministic fixtures.

## Local operations and containers

Use Compose v2 for PostgreSQL/pgvector and, when useful, app containers. Run Ollama natively on Windows unless a verified container setup offers equivalent GPU behavior. Bind services to loopback, use health checks and persistent named volumes, and document backup/restore.

Do not bake models, secrets, private portfolios, or raw licensed documents into images. Container tags/digests and model digests are part of reproducibility evidence.

## Deferred technology

Not approved for MVP: Redis, Celery/RabbitMQ/Kafka, Kubernetes, cloud databases, hosted telemetry, external LLM fallback, native mobile frameworks, brokerage SDKs, or a second search/vector store. Adoption requires a measured bottleneck or new approved scope, failure/privacy analysis, and an architecture decision.

## Decisions to validate at bootstrap

Before writing feature code, record:

- exact Python minor and locked backend package versions;
- exact Node.js LTS, pnpm, Next.js, React, and TypeScript versions;
- PostgreSQL major, pgvector release/image digest, and embedding dimension;
- chosen lint/type/i18n libraries and commands;
- `pandas-ta` availability/license and indicator parity results;
- Ollama/model digests and resource limits on the target GPU;
- public provider outcome (or explicit manual-data fallback);
- decimal precision/scale, accounting convention, timezone/market calendar, and freshness thresholds.

A choice is accepted only when its rationale, version, verification command/test, owner, and upgrade impact are recorded.

## Related documents

- [Documentation guide](README.md)
- [Product scope](00-product-scope.md)
- [Architecture](01-architecture.md)
- [Repository layout](03-repository-layout.md)
