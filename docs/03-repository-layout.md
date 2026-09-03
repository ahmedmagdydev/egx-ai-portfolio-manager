# Repository Layout

## Purpose

This is the exact target layout for future implementation. It expands the [source guide](../EGX_AI_Portfolio_Manager_Implementation_Guide.md) into a modular monorepo while enforcing the boundaries in [architecture](01-architecture.md). The directories below are a specification, not current repository contents; this documentation pass creates no scaffold.

## Target tree

```text
financial-assistant/
├── README.md
├── EGX_AI_Portfolio_Manager_Implementation_Guide.md
├── docs/
│   ├── README.md
│   ├── 00-product-scope.md
│   ├── 01-architecture.md
│   ├── 02-technology-decisions.md
│   ├── 03-repository-layout.md
│   ├── phases/                    # future ordered implementation runbooks
│   └── checklists/                # future shared quality/release gates
├── frontend/
│   ├── app/
│   │   ├── [locale]/
│   │   │   ├── dashboard/
│   │   │   ├── portfolio/
│   │   │   ├── stocks/
│   │   │   │   └── [symbol]/
│   │   │   ├── analysis/
│   │   │   ├── documents/
│   │   │   ├── settings/
│   │   │   └── layout.tsx
│   │   └── globals.css
│   ├── components/
│   │   ├── ui/                    # accessible, domain-neutral primitives
│   │   ├── portfolio/
│   │   ├── stocks/
│   │   ├── documents/
│   │   └── analysis/
│   ├── lib/
│   │   ├── api/                   # generated/checked client and adapters
│   │   ├── i18n/                  # locale/direction/format helpers
│   │   └── validation/
│   ├── messages/
│   │   ├── ar.json
│   │   └── en.json
│   ├── hooks/
│   ├── types/
│   ├── tests/
│   │   ├── unit/
│   │   └── fixtures/
│   ├── e2e/
│   ├── public/
│   ├── package.json
│   ├── pnpm-lock.yaml
│   └── tsconfig.json
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── api/
│   │   │   ├── dependencies.py
│   │   │   ├── errors.py
│   │   │   └── v1/
│   │   ├── core/                  # settings, clock, logging, shared errors
│   │   ├── domain/                # framework-independent entities/value objects
│   │   ├── portfolio/             # ledger, holdings, cash, P&L, allocation
│   │   ├── market/                # normalized quotes/OHLCV and use cases
│   │   ├── finance/               # statements, ratios, financial snapshots
│   │   ├── technical/             # indicators and history-window policy
│   │   ├── documents/             # metadata, extraction, versioning, ingestion
│   │   ├── rag/                   # chunking, embeddings, retrieval, citations
│   │   ├── risk/                  # deterministic portfolio risk
│   │   ├── ai/                    # provider-neutral orchestration and schemas
│   │   ├── tools/                 # typed read/analysis tool registry
│   │   └── infrastructure/
│   │       ├── db/                # SQLAlchemy mappings/repositories/session
│   │       ├── providers/         # public/manual/mock data adapters
│   │       ├── ollama/            # LLM and embedding adapters
│   │       └── files/             # bounded safe local artifact storage
│   ├── migrations/
│   │   ├── versions/
│   │   └── env.py
│   ├── tests/
│   │   ├── unit/
│   │   ├── contract/
│   │   ├── integration/
│   │   ├── ai_eval/
│   │   ├── golden/
│   │   └── fixtures/
│   ├── pyproject.toml
│   └── uv.lock
├── data/
│   ├── raw/                        # ignored local source artifacts
│   ├── processed/                  # ignored reproducible derivatives
│   ├── documents/                  # ignored private/raw document storage
│   ├── imports/                    # ignored user import drop zone
│   └── README.md                   # future policy; no private data
├── scripts/
│   ├── dev/                        # setup/health/seed helpers
│   ├── data/                       # explicit ingestion/reindex jobs
│   └── operations/                 # backup/restore/diagnostics
├── docker/
│   ├── backend/
│   └── frontend/
├── evals/
│   ├── ai/                         # sanitized bilingual evaluation definitions
│   └── retrieval/                  # sanitized relevance judgments
├── docker-compose.yml
├── .env.example
├── .gitignore
└── package-or-task-runner file     # optional, chosen and documented at bootstrap
```

Do not create empty directories preemptively. Add each path only when its owning phase has an implementation artifact or required policy file.

## Ownership by area

### Root

The root contains repository-wide navigation, source brief, local orchestration, safe configuration template, ignore rules, and optional task aliases. It must not accumulate business logic or ad hoc data exports.

### `frontend/`

Owns browser concerns only: routes, localized messages, RTL/LTR presentation, accessible components, chart rendering, form state, and the typed API client. Domain feature folders may compose generic `components/ui` primitives. Financial formulas and provider/model calls are forbidden here.

Arabic translations live in `messages/ar.json`; English in `messages/en.json`. Direction and formatting helpers live in `lib/i18n`. Components must use logical CSS and isolate LTR symbols/numeric technical strings where needed. Tests sit near the frontend but are grouped under `tests`/`e2e` for clear command boundaries.

### `backend/app/`

Each feature package owns its domain rules, application services, interfaces, and feature-specific schemas. The infrastructure package owns concrete external mechanisms. `api` adapts HTTP to use cases; it does not own business logic.

Suggested internal pattern when a feature grows:

```text
feature/
├── domain.py              # entities, values, invariants
├── schemas.py             # internal/use-case contracts, not ORM mappings
├── ports.py               # repository/provider interfaces
├── service.py             # use cases and deterministic policies
└── errors.py              # typed feature failures
```

Do not force this split for a tiny module; split when responsibilities exist. Never create generic `utils.py` dumping grounds. Shared behavior moves to `core` only after two real owners require it and the abstraction is domain-neutral.

### `backend/app/infrastructure/`

Concrete SQLAlchemy, HTTP/parser, file, and Ollama integrations implement inward-defined ports. Provider-specific parsing stays under a provider-named package. Mocks used by runtime/demo may live beside provider contracts; test-only fakes and fixtures remain under tests.

### `backend/migrations/`

Alembic is the sole schema history. Migration filenames use revision plus concise intent. A migration includes extension/index/constraint changes and downgrade behavior where safe. Generated migration output must be reviewed; database dumps never belong here.

### `backend/tests/`

- `unit`: no network/database/model; pure accounting, calculations, policy, and schema tests.
- `contract`: reusable provider/tool contract suites, run against mock and adapters using recorded fixtures.
- `integration`: migrated PostgreSQL/pgvector, repository, API, retrieval, and mocked HTTP/Ollama boundaries.
- `ai_eval`: deterministic harness and assertions around structured output/tool/citation behavior.
- `golden`: human-reviewed expected financial results; changes require explicit rationale.
- `fixtures`: small, sanitized, legally retainable test inputs with source/synthetic status documented.

Test paths should mirror owned modules, for example `backend/tests/unit/portfolio/test_average_cost.py`.

### `data/`

Runtime data is local and ignored. `raw` is immutable-by-policy source material, `processed` is reproducible output, `documents` holds private originals, and `imports` is a bounded intake area. A future tracked `data/README.md` explains retention/provenance/cleanup but contains no private records. Tests never depend on these mutable folders.

### `scripts/`

Scripts are thin, documented entry points into application services. They validate configuration, return nonzero on failure, and support dry-run where destructive. Business rules must remain importable/testable in backend modules. No script silently edits production-like data or embeds credentials.

### `evals/`

Contains sanitized, versioned evaluation case definitions and relevance judgments, separate from test harness code. Arabic/English paired cases include exact symbols, source expectations, timestamps, missing-data cases, and safe-language criteria. Never store a real private portfolio.

## Dependency rules

Allowed direction:

```text
frontend → versioned HTTP contract
API/jobs → application services → domain/ports
infrastructure adapters → domain/ports
AI tools → application services
application services → repositories/providers through ports
```

Forbidden dependencies:

- domain or application modules importing FastAPI route objects, SQLAlchemy mappings, provider parsers, Ollama clients, or frontend code;
- frontend importing backend source or duplicating authoritative financial calculations;
- AI orchestration reading database tables/providers directly instead of typed services/tools;
- one feature reaching into another feature’s infrastructure repository;
- tests relying on live public data for normal execution;
- RAG/library objects leaking into API contracts;
- scripts becoming a second implementation of business behavior.

Use architecture tests/import-lint rules when the scaffold exists to enforce these boundaries.

## Naming conventions

- Python modules/functions/variables: `snake_case`; classes/types: `PascalCase`; constants and enum members: `UPPER_SNAKE_CASE`.
- TypeScript components/types: `PascalCase`; functions/variables: `camelCase`; route folders follow Next.js conventions.
- Database tables/columns/indexes: lowercase `snake_case`; foreign keys named `<entity>_id`; timestamps state their meaning (`observed_at`, `published_at`, `retrieved_at`, `analysis_at`).
- API JSON: `snake_case` to align with backend and source schema; choose once and generate/check clients rather than hand-transform inconsistently.
- EGX symbols: canonical uppercase source-neutral value; never localize or reverse it.
- Money/currency fields: names expose semantics (`price`, `fees`, `currency`), not formatted strings.
- Tests: `test_<behavior>.py` and user-behavior-oriented frontend names; avoid implementation-only names.
- Documents: numbered foundation/runbook names in build order; headings use stable terminology.
- Provider adapters: `<source>_provider`; do not call an adapter “EGX provider” if it represents one particular site.

## API and model placement

Transport request/response schemas belong near `api/v1` or in a clearly owned feature adapter package. Internal domain values remain distinct from persistence and transport forms. OpenAPI output may generate a frontend client into `frontend/lib/api/generated`; generated code is not manually edited.

ORM mappings live only under `infrastructure/db`. Repository ports live with the consuming feature. This avoids one global `models` folder becoming shared mutable ownership.

## Generated and tracked files

### Track

- source code, migrations, documentation, message catalogs;
- exact dependency lockfiles;
- `.env.example` with placeholders/non-secret defaults;
- small sanitized fixtures and golden/evaluation expectations;
- generated API client/schema only if the team chooses checked-in generation, with a reproducibility/staleness check.

### Ignore

- `.env` and local overrides;
- virtual environments, `node_modules`, caches, coverage, browser reports, and build outputs;
- database volumes/dumps except explicitly encrypted local backups outside Git;
- model blobs/Ollama storage;
- `data/raw`, `processed`, `documents`, and `imports` contents;
- real portfolio exports, provider credentials, paid/licensed payloads, and unsanitized logs/prompts.

### Generated-file policy

Every generated artifact has a declared source and command. Prefer regeneration over manual edits. If generated output is committed, CI/local verification must detect drift. Generated files include a header when the format permits. Lockfiles and hand-reviewed migrations are not disposable build output.

## Data and fixture policy

Fixtures must be synthetic or sanitized and legally retainable. Each recorded provider fixture identifies adapter, capture semantics/date, expected currency/timezone, sanitization, and license/terms constraints without embedding credentials. Freeze time in tests. Use obviously fictional portfolio quantities and avoid examples that could be mistaken for current investment advice.

Raw documents preserve hashes and provenance; processed chunks reference the raw/version identity. Never overwrite prior source content silently. Restatements receive new versions.

## Adding a feature: checklist

1. Confirm the feature is in [product scope](00-product-scope.md) and its prerequisite phase is complete.
2. Identify the owning backend feature and frontend route/component; avoid creating a cross-cutting folder first.
3. Define domain terms, deterministic behavior, edge/error/freshness cases, and Arabic/RTL impact.
4. Define or extend inward ports before writing a concrete provider/database/model adapter.
5. Add the smallest migration/API contract needed.
6. Add unit and golden tests, then provider/integration tests; use no mandatory live dependency.
7. Add localized messages, mixed-script/RTL component tests, and relevant Playwright flow.
8. Update documentation and generation outputs through declared commands.
9. Verify dependency rules, secrets/data ignores, provenance, and target-hardware limits.
10. Complete the phase gate before creating dependent modules.

## Current documentation links

- [Documentation guide](README.md)
- [Product scope](00-product-scope.md)
- [Architecture](01-architecture.md)
- [Technology decisions](02-technology-decisions.md)
- [Project README](../README.md)
