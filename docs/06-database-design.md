# 06 — Database Design

## Purpose

This document specifies the PostgreSQL + pgvector schema for the local single-user EGX portfolio assistant. It defines the normalized tables, keys, constraints, indexes, Decimal and timestamp rules, provenance rules, the policy for derived versus persisted data, migrations, backups, and seeding. This is a specification; no migrations or database objects are created during the documentation pass.

## PostgreSQL extensions

Enable and record the following extensions in migrations:

- `pgvector` for document and embedding storage.
- `uuid-ossp` or `pgcrypto` for identifier generation if UUID primary keys are selected.
- `btree_gist` may be useful for exclusion constraints across ranges and timestamps.

Extension versions should be pinned and checked in health probes.

## Naming and typing conventions

1. Primary keys use `id` (UUID or bigserial) with no business meaning.
2. Symbol columns store upper-case normalized tickers such as `COMI`, `FWRY`, `EAST` unless a different convention is explicitly chosen.
3. Monetary values use `NUMERIC(19,4)` or `DECIMAL` types. Avoid `REAL` and `FLOAT` for money, prices, quantities, ratios, and percentages.
4. Quantities use `NUMERIC(19,4)` or `NUMERIC(19,8)` depending on instrument; shares on EGX are integer but intermediate calculations may be fractional for splits and average cost.
5. Timestamps use `TIMESTAMPTZ` stored in UTC. All displayed timestamps are converted by the application or UI to `Africa/Cairo` where appropriate, but storage is UTC.
6. Enumerations are implemented as `TEXT` with `CHECK` constraints in PostgreSQL unless a stable enum type is justified. This keeps schema evolution explicit and avoids opaque OID issues.
7. Every fact table includes `created_at` and `updated_at`.
8. Every source-derived row includes `source`, `source_url` or `source_record_id` where permitted, and `fetched_at`.

## Core schema

### `stocks`

```text
id              UUID PK
symbol          TEXT UNIQUE NOT NULL
name_ar         TEXT
name_en         TEXT
sector          TEXT
industry        TEXT
currency        TEXT NOT NULL DEFAULT 'EGP'
exchange        TEXT NOT NULL DEFAULT 'EGX'
is_active       BOOLEAN DEFAULT true
metadata        JSONB
created_at      TIMESTAMPTZ DEFAULT now()
updated_at      TIMESTAMPTZ DEFAULT now()
```

Indexes on `symbol` (unique already covers), `sector`, `is_active`. `symbol` is the application-level natural key but the PK is `id` to allow future corporate-action identity handling.

### `transactions`

```text
id              UUID PK
stock_id        UUID FK -> stocks(id)
transaction_type TEXT NOT NULL CHECK (...)
quantity        NUMERIC(19,8) NOT NULL CHECK (quantity >= 0 OR transaction_type allows negative)
price           NUMERIC(19,4)
fees            NUMERIC(19,4) NOT NULL DEFAULT 0
amount          NUMERIC(19,4) -- cash impact for non-stock cash movements
currency        TEXT NOT NULL DEFAULT 'EGP'
transaction_date TIMESTAMPTZ NOT NULL
settlement_date TIMESTAMPTZ
notes           TEXT
created_at      TIMESTAMPTZ DEFAULT now()
updated_at      TIMESTAMPTZ DEFAULT now()
```

`transaction_type` allowed values: `BUY`, `SELL`, `DIVIDEND`, `DEPOSIT`, `WITHDRAWAL`, `FEE`. `price` is required for `BUY`/`SELL`, optional for `DIVIDEND`, and irrelevant for `DEPOSIT`/`WITHDRAWAL`/`FEE`. Use `CHECK` constraints to enforce type-specific rules.

Holdings are derived from the transaction ledger; a `holdings` materialized view or table may be maintained for performance but is always reconcilable from `transactions`.

### `cash_accounts`

```text
id              UUID PK
currency        TEXT UNIQUE NOT NULL DEFAULT 'EGP'
balance         NUMERIC(19,4) NOT NULL DEFAULT 0
updated_at      TIMESTAMPTZ DEFAULT now()
```

Cash impacts come from deposits, withdrawals, fees, dividends, and buy/sell settlement. Cash is not a `stock`; treat it as a separate ledger to avoid confusing `symbol` semantics.

### `stock_prices`

```text
id              UUID PK
stock_id        UUID FK -> stocks(id)
symbol          TEXT NOT NULL
timestamp       TIMESTAMPTZ NOT NULL
open            NUMERIC(19,4) NOT NULL
high            NUMERIC(19,4) NOT NULL
low             NUMERIC(19,4) NOT NULL
close           NUMERIC(19,4) NOT NULL
volume          BIGINT NOT NULL
adjusted_close  NUMERIC(19,4)
interval        TEXT NOT NULL DEFAULT '1d'
currency        TEXT NOT NULL DEFAULT 'EGP'
source          TEXT NOT NULL
source_url      TEXT
fetched_at      TIMESTAMPTZ NOT NULL
freshness_state TEXT NOT NULL DEFAULT 'unknown'
created_at      TIMESTAMPTZ DEFAULT now()
UNIQUE (source, symbol, timestamp, interval)
```

Constraint: `low <= open`, `low <= close`, `high >= open`, `high >= close`, `volume >= 0`. Add separate partial indexes for latest quote and history ranges. Store both raw and adjusted close where corporate-action adjustments are known; label the series explicitly.

### `financial_statements`

```text
id              UUID PK
stock_id        UUID FK -> stocks(id)
period_type     TEXT NOT NULL CHECK ('ANNUAL' | 'QUARTERLY' | 'HALF_YEAR' | 'INTERIM')
period          TEXT NOT NULL -- e.g. '2025-Q1'
period_start    DATE
period_end      DATE
revenue         NUMERIC(19,4)
gross_profit    NUMERIC(19,4)
operating_profit NUMERIC(19,4)
net_income      NUMERIC(19,4)
eps             NUMERIC(19,8)
assets          NUMERIC(19,4)
liabilities     NUMERIC(19,4)
equity          NUMERIC(19,4)
cash            NUMERIC(19,4)
operating_cash_flow NUMERIC(19,4)
investing_cash_flow NUMERIC(19,4)
financing_cash_flow NUMERIC(19,4)
shares_outstanding NUMERIC(19,4)
currency        TEXT NOT NULL DEFAULT 'EGP'
source          TEXT NOT NULL
source_url      TEXT
published_at    TIMESTAMPTZ
fetched_at      TIMESTAMPTZ NOT NULL
metadata        JSONB
created_at      TIMESTAMPTZ DEFAULT now()
updated_at      TIMESTAMPTZ DEFAULT now()
UNIQUE (stock_id, period_type, period, source)
```

Restated statements are versioned, not overwritten. Add `statement_version` or `is_restated` if needed. Do not silently replace old statements.

### `documents`

```text
id              UUID PK
stock_id        UUID FK -> stocks(id)
document_type   TEXT NOT NULL CHECK ('ANNUAL_REPORT' | 'QUARTERLY_REPORT' | 'FINANCIAL_STATEMENT' | 'DISCLOSURE' | 'COMPANY_ANNOUNCEMENT' | 'NEWS')
title           TEXT
language        TEXT CHECK ('ar' | 'en' | 'both')
content         TEXT -- extracted normalized text; raw original stored externally or in a separate raw table/blob
checksum        TEXT NOT NULL
source          TEXT NOT NULL
source_url      TEXT
published_at    TIMESTAMPTZ
fetched_at      TIMESTAMPTZ NOT NULL
metadata        JSONB
created_at      TIMESTAMPTZ DEFAULT now()
updated_at      TIMESTAMPTZ DEFAULT now()
```

The `content` field holds the extracted/cleaned text used for chunking. The original file/blob is stored under `DOCUMENTS_DIR` or a `document_blobs` table with a content hash, never modified after ingestion.

### `document_chunks`

```text
id              UUID PK
document_id     UUID FK -> documents(id)
chunk_index     INTEGER NOT NULL
content         TEXT NOT NULL
embedding       vector(...) -- dimension chosen to match embedding model
metadata        JSONB
page_or_section TEXT
span_start      INTEGER
span_end        INTEGER
created_at      TIMESTAMPTZ DEFAULT now()
UNIQUE (document_id, chunk_index)
```

Build a vector index appropriate to the expected row count and similarity operator (`ivfflat` or `hnsw`). Keep `embedding` generation separate from storage so the dimension can be configured.

### `ai_analyses`

```text
id              UUID PK
analysis_type   TEXT NOT NULL
request_hash    TEXT -- for idempotency/cache invalidation
input_snapshot  JSONB NOT NULL
output          JSONB NOT NULL
model_name      TEXT
prompt_metadata JSONB -- safe metadata only, no raw user secrets
data_as_of      TIMESTAMPTZ
sources         JSONB
created_at      TIMESTAMPTZ DEFAULT now()
```

Store enough to audit the response and reproduce the input snapshot, but not raw prompts or document contents if they contain private data. Analysis types include `stock`, `portfolio`, `risk`, `chat`.

### `settings` or `app_settings`

```text
id              UUID PK
key             TEXT UNIQUE NOT NULL
value           JSONB NOT NULL
updated_at      TIMESTAMPTZ DEFAULT now()
```

Stores runtime risk limits, feature flags, last successful provider refresh, and exchange calendar hints.

## Derived versus persisted data policy

1. The transaction ledger is the source of truth for portfolio state.
2. `holdings` may be materialized for read performance but must be recomputed deterministically from `transactions`.
3. P&L, allocations, financial ratios, and technical indicators are computed on demand or cached with a `computed_at` timestamp and the inputs hash. Caches must be invalidated by changes to underlying data.
4. Do not store LLM-generated numbers as authoritative. Store the structured AI response with source references and `data_as_of`; the numbers inside must be reproducible from deterministic services.
5. Source raw records are preserved where legally/space permitted. Normalized values never overwrite raw provenance.

## Migrations

Use Alembic or the chosen migration tool. Rules:

- Every schema change is a migration.
- Migration files are committed.
- Migrations are reversible unless an irreversible operation is explicitly documented and approved.
- Test migrations against a throwaway database before applying to the local dev database.
- Include seed data for stocks, a sample portfolio, and fixtures only in development; seed is skipped or minimal in production-like contexts.
- The `pgvector` extension and indexes are created by migrations, not manual SQL.

## Backups

1. Use `pg_dump` to create compressed backups into `BACKUPS_DIR`.
2. Schedule backups before risky schema changes.
3. Document restore procedure and test it at least once before release.
4. Backed-up `documents` directory must be included because large binary files may not be in the database.
5. Do not back up private data to cloud storage unless the user explicitly configures it.

## Seeding

Seeding provides:

- A small list of active EGX symbols with Arabic/English names and sectors.
- Synthetic transactions and cash movements for manual testing.
- Deterministic market fixtures for the mock provider.
- Sample financial statements for one or two symbols.

Seed data must be clearly synthetic and must not include real user portfolios. Seed scripts are separate from production migration data.

## Data provenance

Every row from an external source must contain:

- `source` — short identifier like `mock`, `public_web`, `manual_csv`.
- `source_url` or `source_record_id` where available.
- `fetched_at` — UTC timestamp of retrieval.
- `published_at` or `market_timestamp` where applicable.
- `freshness_state` — `fresh`, `stale`, `unknown`.

Freshness is computed by the application using configured thresholds and exchange/session semantics, not by the source alone. Records may not be silently updated; conflicts create new versions or quarantine records.

## Security and privacy

1. Database runs locally or in a Docker container with no public exposure.
2. Connection string contains credentials in the ignored `.env` file.
3. Backups are stored outside source control in `BACKUPS_DIR`.
4. Document content may contain MNPI; keep local and encrypted-at-rest if the OS supports it. Do not transmit documents to external services unless explicitly configured and audited.

## Acceptance checklist

- [ ] PostgreSQL + pgvector extensions are created by versioned migrations.
- [ ] All monetary columns are `NUMERIC`/DECIMAL, not `REAL`/`FLOAT`.
- [ ] All timestamps are `TIMESTAMPTZ` stored in UTC.
- [ ] Transactions table supports all required types with appropriate constraints.
- [ ] Holdings are derivable from the transaction ledger.
- [ ] `stock_prices` enforces OHLCV invariants and source uniqueness.
- [ ] `financial_statements` supports period versioning and does not overwrite restated statements.
- [ ] `documents` and `document_chunks` preserve source, language, and publication metadata.
- [ ] Embeddings use a configurable `vector(dim)` dimension.
- [ ] Derived data can be recomputed and is not treated as authoritative over the ledger.
- [ ] Backups include both the database and external document blobs.
- [ ] Seed data is synthetic and clearly marked as such.
