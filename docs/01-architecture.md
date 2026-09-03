# Architecture

## Architectural style

Use a **local modular monolith**: one Next.js web application, one FastAPI application divided into explicit modules, one PostgreSQL/pgvector database, and local Ollama model services. This matches the target hardware and single-user scope while preserving replaceable interfaces at volatile boundaries.

Do not introduce microservices, message brokers, Kubernetes, a separate vector database, distributed caches, or cloud services without measured need. Long-running ingestion may begin as an explicit local command/job; adding a queue is a later decision.

See [product scope](00-product-scope.md), [technology decisions](02-technology-decisions.md), and [repository layout](03-repository-layout.md).

## System context

```text
                    Local user
                 Arabic / English
                        │
                        ▼
              Next.js browser UI
   portfolio · stocks · documents · chat · settings
                        │ typed HTTP/stream contract
                        ▼
                 FastAPI modular API
 ┌──────────────┬─────────────┬────────────┬──────────────┐
 │ Portfolio    │ Research    │ Documents  │ AI/tool      │
 │ & risk       │ engines     │ & retrieval│ orchestration│
 └──────┬───────┴──────┬──────┴─────┬──────┴──────┬───────┘
        │              │            │             │
        ▼              ▼            ▼             ▼
 PostgreSQL +      Provider       pgvector     Ollama local API
 pgvector          adapters       retrieval    reasoning/embedding
                        │
                        ▼
      validated public sources / manual imports / fixtures
```

All components bind locally by default. The browser talks to the API; it never calls market sources, PostgreSQL, or Ollama directly.

## Component responsibilities

### Next.js UI

Owns routing, localized presentation, form interaction, API client calls, accessible loading/error/stale states, charts, and Arabic/RTL layout. It does not contain portfolio accounting formulas, source credentials, provider parsing, retrieval logic, or prompts that define backend safety.

The UI formats locale-neutral API data for `ar-EG` or English. It preserves LTR islands for ticker symbols, code, formulas, URLs, and timestamps. Direction is applied at a high-level container and all views are tested in both directions.

### FastAPI transport layer

Owns API versioning, request validation, authentication hooks if later introduced, response/error envelopes, correlation IDs, pagination, and serialization. Route handlers remain thin: validate, authorize (future), call an application service, and map the result. They do not query provider HTML or calculate P&L directly.

### Deterministic domain/application services

Own portfolio ledger semantics, financial ratios, technical indicators, risk calculations, freshness decisions, and use-case orchestration. Money uses decimal types and explicit rounding. Time-dependent services receive a clock/analysis timestamp so tests and backtests are reproducible.

Domain results distinguish raw facts, calculated values, unavailable inputs, and validation errors. Calculations must remain usable without Ollama.

### Persistence

PostgreSQL owns transactional records, normalized reference/research data, provenance, document metadata/content references, embeddings through pgvector, application settings, and audit-relevant analysis metadata. Migrations are the only supported schema-change mechanism.

Holdings may be materialized for performance, but the transaction ledger is authoritative and any derived state must be reproducible/reconcilable. Raw source records/documents are preserved where licensing and storage permit; normalized values never erase provenance.

### Provider adapters

Interfaces define quotes/history, financial data, news/disclosures, LLM generation, and embeddings. Adapters translate source-specific behavior into normalized internal contracts. Public providers must report source, currency, observed/published/retrieved times, delay/freshness, and failures.

A mock provider and sanitized fixtures are mandatory. A public web adapter cannot be declared production-ready until access permission/terms, robots rules where applicable, semantics, reliability, rate limits, coverage, and parser risks have been validated. Provider failure returns an explicit typed error or stale cached result marked as stale.

### Document ingestion and RAG

Ingestion preserves original source metadata, extracts Arabic/English text, normalizes without destroying evidence, deduplicates, chunks prose, and treats financial tables specially. Embeddings are generated separately from reasoning and stored with metadata filters.

Retrieval returns evidence objects with source, title, publication date, symbol, document type, and page/section when available. Retrieved content is untrusted data and cannot override application/system instructions.

### AI and tool orchestration

The LLM provider isolates Ollama. A typed tool registry grants read/analysis capabilities only—there is no trade tool. The orchestrator validates tool arguments/results, sets iteration/time limits, records tool metadata without secrets, handles unavailable dependencies, and emits a structured analysis schema.

The model receives deterministic calculations and retrieved evidence, then provides interpretation. It cannot become the source for prices, ratios, indicators, portfolio values, limits, or citations.

## Dependency direction

```text
API routes / CLI jobs
          ↓
Application use cases
          ↓
Domain models and deterministic policies
          ↑
Persistence, provider, clock, model, and embedding interfaces
          ↑
Concrete PostgreSQL / public source / Ollama adapters
```

- Domain code depends on no web framework, ORM model, provider parser, UI type, or LLM SDK.
- Application services depend on interfaces, not concrete adapters.
- Adapters may depend inward on interface/domain types; inward modules never import adapters.
- AI tools call application services; they do not bypass validation to query tables or websites.
- Frontend types should be generated from or checked against the API contract, not imported from Python source.
- Cross-module database access goes through the owning service/repository contract.

## Core data paths

### Transaction to portfolio view

1. UI submits a locale-neutral typed transaction; localized text is presentation only.
2. API validates symbol, type, decimal quantity/price/fees, date, and idempotency input.
3. Portfolio service applies ordering, cash, oversell, and accounting rules in one database transaction.
4. Ledger data is committed; derived holdings are recomputed or updated and reconciled.
5. Read service combines holdings with a quote carrying source/freshness.
6. Deterministic services calculate value, P&L, and allocation.
7. API returns values plus currency, timestamps, freshness, and unavailable warnings.
8. UI formats for the active locale/direction without recalculation.

### Stock analysis

1. Request identifies symbol and analysis timestamp.
2. Services fetch latest eligible quote, statements, OHLCV, disclosures/news, and current position.
3. Deterministic engines calculate ratios, indicators, and portfolio impact.
4. Retrieval selects evidence using symbol/date/source filters.
5. Orchestrator passes typed facts/evidence to Qwen through tools.
6. Schema validation enforces recommendation enum, reasons, risks, missing information, `data_as_of`, and sources.
7. UI labels facts/calculations/retrieval/interpretation and shows stale/partial status.

If any required fact is missing, analysis reports it; the model must not fill it from memory.

### Document ingestion and retrieval

```text
source fetch/manual import
  → validate type/size and capture provenance
  → preserve raw artifact where allowed
  → extract language-aware text and tables
  → deduplicate/version
  → chunk (target initially 800–1200 tokens, 100–200 overlap)
  → embed in bounded batches
  → store vector + metadata
  → retrieve with point-in-time filters
  → return cited evidence
```

Malformed or hostile documents are quarantined/failed explicitly. Embedded instructions are content, not authority.

### Historical evaluation

An analysis timestamp is injected into every repository/provider query. Only observations and documents available by that timestamp are eligible. Recommendation inputs and versions are captured for reproducibility. Future prices are joined only after analysis output is fixed to calculate evaluation metrics.

## Data and time rules

- Persist timestamps with timezone; store/compare in UTC and render in the chosen locale/time zone.
- Distinguish market observation time, source publication time, retrieval/ingestion time, and analysis time.
- Preserve source currency; MVP calculations require EGP and reject/segregate unsupported currencies rather than silently convert.
- Store monetary and quantity values as fixed/controlled precision decimals. Define precision and rounding before migrations.
- A freshness policy belongs to application configuration by data type and market session; “latest row” is not automatically “current.”
- Restated statements/documents are versioned and never silently overwrite historical knowledge.

## Failure and degraded modes

| Failure | Required behavior |
|---|---|
| Public market source unavailable/rate-limited | Serve eligible cached data with a visible stale marker, or return unavailable; never relabel it current. |
| Parsing/schema drift | Reject/quarantine the payload, log source/parser metadata, retain last known data with its original timestamp. |
| PostgreSQL unavailable | Fail readiness and block writes/analysis requiring persisted facts; do not start an in-memory shadow portfolio. |
| Ollama unavailable or resource constrained | Portfolio/research views continue; AI analysis reports unavailable and may be retried. |
| Embedding model unavailable | Preserve queued/imported document metadata/raw content; retrieval remains at last completed index or reports unavailable. |
| Partial evidence | Produce a partial result only when clearly labeled, with missing fields and no fabricated recommendation support. |
| Malicious document prompt | Treat as quoted content; do not alter tools, system rules, or execution. |
| RTL/localization defect | Core data remains intact; the affected flow does not pass release acceptance until bilingual accessibility tests pass. |

## Local deployment topology and resources

Docker Compose is intended for PostgreSQL/pgvector and may run the app services later; Ollama can run natively to use the NVIDIA GPU reliably. Bind database and model ports to loopback unless explicitly needed. Use persistent volumes for the database and controlled local paths for raw documents/backups.

The 16 GB RAM/6 GB VRAM target requires one modest reasoning model (`qwen3.5:9b`), a quantized embedding model, bounded context, bounded embedding batches, limited concurrent generations, and ingestion scheduled away from interactive inference where necessary. Do not load 27B+ models on the target machine as the default.

## Security and privacy boundaries

- Credentials exist only in local environment/secret configuration and backend adapters.
- Browser bundles contain no database, provider, or model secrets.
- Logs include correlation ID, source, timestamps, tool name/status, and errors but exclude secrets, full private documents, unnecessary prompts, and portfolio exports.
- Inputs, fetched content, filenames, URLs, and model/tool arguments are validated and bounded.
- File ingestion protects against path traversal, oversized files, unsupported content, and active content.
- Default local trust does not justify exposing services to the LAN; authentication must precede broader binding.

## Architectural invariants

1. No automated trade execution capability.
2. No LLM-originated financial fact.
3. No current value without provenance and freshness.
4. No provider lock-in; mocks are first-class.
5. No AI dependency in deterministic portfolio/research engines.
6. No direct browser access to secrets, database, Ollama, or external providers.
7. No future data in point-in-time evaluation.
8. No silent replacement of old source information or unsupported accounting behavior.
9. No arbitrary unvalidated AI response where a structured schema is required.
10. No second infrastructure component when the modular monolith and PostgreSQL can meet the measured need.
11. Arabic functionality and RTL accessibility are release requirements, not optional polish.

## Verification gates

Before implementation crosses each boundary, verify:

- unit tests prove deterministic formulas and edge cases;
- adapters pass a common contract against mock/recorded fixtures;
- integration tests prove migrations, persistence, pgvector retrieval, and Ollama isolation;
- API tests prove envelope, validation, provenance, and stale/missing behavior;
- Playwright flows cover Arabic/English, RTL/LTR, keyboard access, mixed-script values, and error states;
- fixed AI evaluations prove tool use, numerical fidelity, citations, missing-evidence behavior, and Arabic quality;
- resource tests fit target hardware and failures degrade as specified.
