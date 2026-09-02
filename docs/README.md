# Documentation Guide

This directory turns the [original implementation guide](../EGX_AI_Portfolio_Manager_Implementation_Guide.md) into implementation-oriented foundations. The source guide remains the product brief; these documents clarify scope, boundaries, decisions, and ownership without replacing it.

## Reading order

| Order | Document | Question answered | Exit condition |
|---:|---|---|---|
| 0 | [Product scope](00-product-scope.md) | What are we building, for whom, and what is deferred? | MVP and safety boundaries are understood. |
| 1 | [Architecture](01-architecture.md) | Which component owns each responsibility and how does data flow? | No numerical or infrastructure responsibility is assigned to the LLM. |
| 2 | [Technology decisions](02-technology-decisions.md) | Which tools are preferred, why, and what must be validated? | Bootstrap choices can be pinned without adding unnecessary infrastructure. |
| 3 | [Repository layout](03-repository-layout.md) | Where will implementation artifacts live and what may they depend on? | New work has a clear owner and test location. |
| 4 | [Local environment](04-local-environment.md) | How is the target Windows machine prepared and verified? | Toolchains, Docker, PostgreSQL, GPU, and Ollama checks are understood. |
| 5 | [Configuration and secrets](05-configuration-and-secrets.md) | How are settings, limits, and credentials managed safely? | Configuration ownership and validation rules are fixed. |
| 6 | [Database design](06-database-design.md) | How are source data, transactions, documents, and vectors persisted? | Types, constraints, provenance, migrations, and backup rules are fixed. |
| 7 | [API contracts](07-api-contracts.md) | How do frontend and backend exchange typed data and errors? | Endpoint, freshness, pagination, and error conventions are fixed. |
| 8 | [Data providers](08-data-providers.md) | How will public EGX sources be validated and kept replaceable? | Provider contracts, validation spike, mocks, and fallbacks are defined. |
| 9 | [Financial safety](09-financial-safety.md) | Which numerical and AI safety rules are non-negotiable? | Precision, freshness, evidence, and recommendation rules are fixed. |
| 10 | [Testing and quality](10-testing-and-quality.md) | What evidence is required at every test layer? | Quality gates and bilingual evaluation expectations are defined. |
| 11 | [Observability and operations](11-observability-and-operations.md) | How is the local system monitored, recovered, and resource-limited? | Logging, health, backup, recovery, and hardware policies are defined. |
| 12 | [Phase runbooks](phases/00-bootstrap.md) | In what exact order is the application implemented? | Runbooks 00–12 are executed sequentially. |
| — | [Milestones](milestones.md) | How is user-visible delivery grouped and gated? | The current milestone and go/no-go evidence are known. |
| — | [Decision log](decision-log.md) | Which choices are accepted, proposed, or deferred? | Open decisions are visible rather than implicit. |
| — | [Traceability matrix](traceability-matrix.md) | Where is every source-guide requirement implemented and verified? | Every material requirement has an owner and evidence target. |
| — | [Phase DoD](checklists/phase-definition-of-done.md) / [release checklist](checklists/release-checklist.md) | What must be signed off? | Required evidence is recorded before progression or release. |
| — | [Source guide](../EGX_AI_Portfolio_Manager_Implementation_Guide.md) | What detailed phases, features, and safety principles originated the project? | Relevant source requirements have been reviewed before implementation. |

Return to the [project README](../README.md) for the project overview and shortest path to the first milestone.

## Dependency graph

```text
Product scope
    ↓
Architecture
    ↓
Technology decisions
    ↓
Repository layout
    ↓
Environment → Configuration → Database/API/Providers/Safety/Quality/Operations
    ↓
Portfolio core → Market data → Financials → Technical analysis
    ↓
Documents/RAG → Ollama/tools → Portfolio AI → Risk
    ↓
Full dashboard → AI chat → Backtesting/evaluation → Release
```

Work may be researched in parallel, but implementation gates are sequential where facts depend on preceding layers. In particular:

- portfolio accounting precedes AI;
- provider contracts and mocks precede reliance on live market data;
- normalized, provenance-bearing documents precede RAG;
- typed deterministic tools precede model orchestration;
- the complete dashboard follows stable backend contracts;
- backtesting uses point-in-time data and must prevent look-ahead bias.

A thin portfolio UI may be delivered after the portfolio backend is stable to satisfy the first milestone. This is not permission to build the full dashboard early.

## Five milestone checklist

### 1. Deterministic portfolio

- [ ] Reproducible local services and health checks.
- [ ] Migrated portfolio database.
- [ ] Deterministic transaction, cash, holding, cost, P&L, and allocation behavior.
- [ ] Unit/golden tests for fees, partial sales, ordering, and invalid transactions.
- [ ] Typed portfolio API and thin usable portfolio UI.
- [ ] No LLM dependency.

### 2. Reliable stock snapshot

- [ ] Replaceable market provider plus mock fixtures.
- [ ] Public-source terms, timestamps, currency, coverage, rate limits, and parsing stability validated before adoption.
- [ ] Financial statement ingestion and deterministic ratios.
- [ ] Technical indicators with warm-up and insufficient-history behavior.
- [ ] Stock view exposes source, timestamp, freshness, and unavailable states.

### 3. Cited document retrieval

- [ ] Original documents preserved with source, language, and publication time.
- [ ] Safe bilingual extraction, deduplication, and table-aware chunking.
- [ ] Embeddings stored in pgvector with metadata filters.
- [ ] Retrieval answers cite title, source, publication date, and page/section where available.

### 4. Tool-grounded AI analysis

- [ ] Local Ollama provider isolated behind an interface.
- [ ] Typed tools retrieve portfolio, market, financial, technical, news, and document facts.
- [ ] Structured five-dimension analysis reports risks, missing evidence, sources, and `data_as_of`.
- [ ] Arabic and English outputs pass fixed evaluations.
- [ ] Tool/model failure degrades safely; no trades can be executed.

### 5. Risk and evidence-based maturity

- [ ] Deterministic concentration and statistical risk metrics.
- [ ] Configured—not invented—portfolio limits.
- [ ] Point-in-time backtests prevent future-data leakage.
- [ ] AI evaluations cover numerical accuracy, citations, hallucination, tool use, reasoning, and Arabic quality.
- [ ] Backup/restore, privacy, resource, degraded-mode, and release checks pass.

## How to use the phase runbooks

For each implementation phase, the developer should:

1. Read the source-guide section and all linked foundational contracts.
2. Confirm prerequisites and unresolved decisions; do not silently choose ambiguous accounting or data semantics.
3. Create only the modules owned by that phase, respecting the documented dependency direction.
4. Implement deterministic behavior before adapters, UI, or AI wrappers.
5. Add unit, contract, integration, and manual demonstration evidence as applicable.
6. Verify errors, stale/missing data, provenance, logging privacy, and rollback/recovery behavior.
7. Complete the phase Definition of Done before starting a dependent phase.

Every runbook contains: objective, prerequisites, expected modules, schema/API impact, algorithms and edge cases, ordered tasks, automated tests, manual demo, observability, failure handling, recovery/rollback, and an acceptance checklist.

## Shared Definition of Done

A phase is complete only when:

- required behavior works and has automated tests;
- errors and unavailable data are explicit;
- data models and API contracts are documented;
- setup and verification are reproducible locally;
- provenance and timestamps survive end to end;
- secrets and private portfolio data do not enter Git or logs;
- Arabic/RTL behavior is checked wherever UI or generated language changes;
- the feature works without an LLM unless the phase explicitly introduces one;
- no dependent phase has been used to conceal incomplete foundational behavior.

## Documentation maintenance

Use stable terms: **symbol**, **quote**, **OHLCV**, **transaction**, **holding**, **statement period**, **publication time**, **document chunk**, **recommendation**, and **analysis timestamp**. Update links and acceptance gates whenever a document moves. Architectural uncertainty belongs in an explicit decision record during future documentation work; it must not be embedded as an undocumented implementation assumption.
