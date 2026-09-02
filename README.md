# EGX AI Portfolio Manager

A local-first, single-user investment research and portfolio decision-support application for the Egyptian Exchange (EGX). It combines deterministic portfolio and financial calculations, timestamped market data, company documents, retrieval-augmented generation (RAG), and a locally hosted bilingual reasoning model.

> **Safety boundary:** This project is not a broker, trading bot, or source of guaranteed returns. It must never place orders automatically. Numerical facts must come from validated data or deterministic application services—not model memory. Every analysis must expose data freshness, sources, missing information, and material risk.

## Status

The repository is in **Phase 00 — local bootstrap**. The FastAPI and Next.js shells, local PostgreSQL/pgvector service, health contracts, migrations, and baseline verification are scaffolded. Product features, business tables, and LLM integration are intentionally deferred. The original product brief is preserved unchanged in [`EGX_AI_Portfolio_Manager_Implementation_Guide.md`](EGX_AI_Portfolio_Manager_Implementation_Guide.md).

The initial operating assumptions are:

- local deployment on one Linux development VM;
- one trusted user, with authentication deferred;
- EGX-listed securities and EGP as the MVP market/currency boundary;
- no external LLM API required for core operation;
- a replaceable market-data provider, with no public web source treated as production-ready until its terms, semantics, coverage, and reliability are validated;
- Arabic and English user experiences, including complete right-to-left (RTL) behavior for Arabic.

## Target machine and prerequisites

The design can be developed on this Linux VM without a GPU or Ollama. Local bootstrap requires:

- Git;
- Node.js and a package manager;
- Python 3.11 or newer;
- Docker Engine and Compose (or an equivalent local PostgreSQL installation);
- `qwen3.5:9b` for reasoning and `qwen3-embedding:4b-q4_K_M` for embeddings.

Exact versions are recorded in [`docs/versions.md`](docs/versions.md). Ollama and GPU checks are optional for this phase and are not required by the API or tests.

## Documentation map

Read these documents in order:

1. [Documentation index](docs/README.md) — reading order, dependencies, milestones, and documentation usage.
2. [Product scope](docs/00-product-scope.md) — users, MVP boundaries, bilingual UX, safety, and measurable outcomes.
3. [Architecture](docs/01-architecture.md) — local topology, responsibilities, flows, failure behavior, and invariants.
4. [Technology decisions](docs/02-technology-decisions.md) — selected stack, rationale, alternatives, and decisions still requiring validation.
5. [Repository layout](docs/03-repository-layout.md) — target tree, ownership, dependencies, naming, and file policies.
6. [Environment and shared contracts](docs/04-local-environment.md) — continue through documents 04–11 for setup, configuration, database, API, providers, safety, testing, and operations.
7. [Phase runbooks](docs/phases/00-bootstrap.md) — execute phases 00–12 in order, using each phase's acceptance gate.
8. [Milestones](docs/milestones.md) and [traceability matrix](docs/traceability-matrix.md) — track delivery and coverage of the source requirements.
9. [Original implementation guide](EGX_AI_Portfolio_Manager_Implementation_Guide.md) — authoritative source brief and detailed phase inventory.

## Shortest path to the first milestone

Implementation must proceed in dependency order and must not introduce AI before deterministic portfolio behavior is stable:

1. Pin toolchain versions and establish reproducible local health checks.
2. Start PostgreSQL with pgvector and create migrations rather than editing schemas manually.
3. Implement stock, transaction, holding, and cash models with explicit EGP precision and ordering rules.
4. Implement and unit-test average cost, realized/unrealized P&L, market value, and allocation calculations.
5. Add a mock market-data provider; validate any public-web adapter separately before relying on it.
6. Expose typed FastAPI portfolio endpoints.
7. Add only the thin portfolio UI needed to enter BUY/SELL transactions and inspect holdings and allocations.
8. Demonstrate deterministic results from a fixed transaction fixture, including fees and partial sales.

The first milestone is complete only when a user can add stocks and transactions and reliably view holdings, average cost, market value, P&L, and portfolio/sector allocation. Ollama, RAG, recommendations, and full dashboard features remain disabled at this point.

## Non-negotiable engineering rules

- Use decimal financial arithmetic with an explicitly documented rounding policy; never use binary floating point for money.
- Preserve source, observation/publication timestamp, currency, and freshness status with market and financial data.
- Label verified facts, calculated metrics, retrieved evidence, assumptions, and model interpretation distinctly.
- Return an explicit unavailable/stale state rather than silently substituting invented or old data.
- Keep frontend, API, deterministic domain services, providers, persistence, retrieval, and LLM orchestration separated.
- Keep provider and LLM interfaces replaceable and test them with mocks/fixtures.
- Treat retrieved documents as untrusted content that cannot override system or tool rules.
- Keep secrets and private portfolio exports out of source control and logs.
- Evaluate Arabic quality, RTL presentation, citations, tool use, and numerical accuracy before release.

## Contributing during the documentation stage

Preserve the source guide. Record assumptions and unresolved choices explicitly rather than presenting guesses as accepted decisions. Keep relative links valid, terminology consistent, and implementation instructions testable. Any future implementation change should trace back to scope, an architecture boundary, a technology decision, and an acceptance gate.

## Local workflows

From the repository root, `make install` creates the pinned Python 3.11 virtual environment, installs backend dependencies, freezes `backend/requirements.lock.txt`, copies `.env.example` to `.env` when needed, and runs `npm ci`. Start PostgreSQL with `make db-up`, then run `make migrate` (safe to repeat). Use separate terminals for `make backend` and `make frontend`, or run the commands in the background.

Run `make lint`, `make typecheck`, `make test`, and `make test-integration` (the latter requires PostgreSQL). `make build` validates the frontend production build. Stop services with `make stop`; `make db-down` removes the Compose container but preserves the named volume. `CONFIRM=yes make reset` removes the volume and all local database data after printing a destructive warning.

Troubleshooting: if Docker is unavailable, start Docker or use a local PostgreSQL configured from `.env`; a port collision should be resolved by changing the corresponding local port and restarting; interrupted model pulls can be retried later; Ollama health is intentionally separate and the application remains usable without it, including CPU-only Ollama fallback. PowerShell equivalents are `Copy-Item .env.example .env`, `docker compose up -d postgres`, `python -m alembic -c backend/alembic.ini upgrade head`, and the corresponding `npm`/`uvicorn` commands.
