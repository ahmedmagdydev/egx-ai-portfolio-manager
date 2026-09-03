# 05 — Configuration and Secrets

## Purpose

This document defines the configuration hierarchy, the `.env.example` contract, non-secret defaults, risk-limit settings, safe paths and logging controls, and the rules that prevent secrets and private portfolio data from entering Git, logs, or frontend bundles.

## Scope

This documentation pass does not create any `.env` file, credentials, or configuration files. It provides the contract the implementation must follow so a single developer can reproduce the local environment without leaking sensitive data.

## Configuration principles

1. Secrets are injected through the environment. Code reads settings through a validated configuration object, never from scattered `os.environ` calls or raw `process.env` access in business logic.
2. Non-sensitive defaults and structure live in versioned configuration files, not environment variables.
3. Public and local-only bindings are defaults; sensitive, per-installation, and tunable values are environment overrides.
4. Portfolio data, real account identifiers, brokerage credentials, and live API keys are not stored in repository files.
5. Logs and API responses never emit secrets or private portfolio balances except to the authenticated local user through safe channels. In the MVP, this means no secret reaches the browser or logs.

## Configuration hierarchy

Precedence from strongest to weakest:

1. Runtime environment variables (`.env` file or shell exports during local development).
2. Application-level validated settings object in the backend (Pydantic Settings pattern) and equivalent typed config in the frontend (only `NEXT_PUBLIC_*` for non-sensitive runtime URLs).
3. Versioned environment-specific YAML/JSON/TOML files containing non-secret defaults such as exchange calendar hints, supported symbols, or UI labels.
4. Hard-coded safe defaults for ports, timeouts, and local-only bindings.

No stage of the hierarchy may bypass validation. Invalid configuration must fail fast with a clear error before the server starts.

## Environment file contract

A root `.env.example` must be committed. It lists every variable, whether it is required, its default, and its purpose. A `.env` file copied from the example is ignored by Git and populated locally. The example must never contain real values, keys, or portfolio data.

### Suggested `.env.example` sections

```text
# Local application binding (loopback only by default)
BACKEND_HOST=127.0.0.1
BACKEND_PORT=8000
NEXT_PUBLIC_API_BASE=http://127.0.0.1:8000

# CORS origins (loopback only for local single-user)
CORS_ALLOWED_ORIGINS=http://127.0.0.1:3000,http://localhost:3000

# PostgreSQL connection (Docker default; change only for non-container DB)
DATABASE_URL=postgresql+asyncpg://postgres:changeme@127.0.0.1:5432/egx_portfolio
POSTGRES_USER=postgres
POSTGRES_PASSWORD=changeme
POSTGRES_DB=egx_portfolio

# Alembic / migrations use the same DATABASE_URL; synchronous fallback is documented
# SYNC_DATABASE_URL=postgresql+psycopg://postgres:changeme@127.0.0.1:5432/egx_portfolio

# pgvector extension version target
PGVECTOR_TARGET_VERSION=0.8.0

# Ollama (loopback, no external exposure)
OLLAMA_BASE_URL=http://127.0.0.1:11434
OLLAMA_GENERATION_MODEL=qwen3.5:9b
OLLAMA_EMBEDDING_MODEL=qwen3-embedding:4b-q4_K_M
OLLAMA_REQUEST_TIMEOUT=120
OLLAMA_EMBEDDING_BATCH_SIZE=16
OLLAMA_MAX_CONTEXT_TOKENS=4096

# Optional external LLM fallback; leave unset if unused
# EXTERNAL_LLM_API_KEY=your-key-here
# EXTERNAL_LLM_BASE_URL=https://...

# Logging (no private data)
LOG_LEVEL=INFO
LOG_FORMAT=json

# Paths for local file artifacts (relative paths are resolved from repo root)
DATA_DIR=./data
DOCUMENTS_DIR=./data/documents
IMPORTS_DIR=./data/imports
BACKUPS_DIR=./data/backups

# Market-data provider selection
# Allowed values: mock, public_web (only after validation spike), manual_csv
MARKET_PROVIDER=mock

# Public web market-data source (optional until validated)
# PUBLIC_WEB_PROVIDER_BASE_URL=https://...
# PUBLIC_WEB_PROVIDER_API_KEY=optional-key-if-source-requires-one
# PUBLIC_WEB_PROVIDER_RATE_LIMIT_PER_SECOND=1
# PUBLIC_WEB_PROVIDER_RETRY_MAX_ATTEMPTS=3

# Freshness thresholds (in minutes unless otherwise noted)
QUOTE_FRESHNESS_MINUTES=15
HISTORY_FRESHNESS_MINUTES=60

# Portfolio risk limits (percentages are numeric 0-100 or decimal fraction depending on schema; must match DB)
MAX_SINGLE_POSITION_PERCENT=25.0
MAX_SECTOR_EXPOSURE_PERCENT=40.0
MIN_CASH_PERCENT=10.0

# Default currency and exchange assumptions
DEFAULT_CURRENCY=EGP
DEFAULT_EXCHANGE=EGX

# Feature flags for local single-user
AUTH_ENABLED=false
AUTO_TRADING_ENABLED=false
```

Add comments or `DO_NOT_COMMIT` markers where a developer might be tempted to paste a real key.

## Backend configuration object

The FastAPI application must read settings at import time once. Use a Pydantic Settings class that:

- validates types and required fields,
- coerces URLs and paths,
- enforces local-only default bindings,
- supports `Decimal` conversion for monetary configuration,
- distinguishes development-local defaults from production defaults,
- fails on unknown fields or invalid ranges, and
- redacts secrets in `__repr__` and in exported config-dump endpoints.

The settings object is the single source for:

- database connection string,
- Ollama endpoint and model names,
- CORS origins (default loopback),
- log level and format,
- file paths,
- provider selection,
- freshness thresholds,
- risk limits,
- feature flags.

No business module should import `os` to look up a variable.

## Frontend configuration rules

The Next.js build may only use `NEXT_PUBLIC_` for non-sensitive runtime constants such as the API base URL. All secrets, API keys, and credentials remain server-side. The frontend receives data through authenticated or local trusted API calls only.

## Secrets management

1. Store secrets in the ignored `.env` file.
2. Never commit `.env`, `.env.local`, `.env.production`, database credential files, or provider API keys.
3. `.gitignore` must include:
   - `.env`
   - `.env.*.local`
   - `*.pem`, `*.key`
   - `data/`
   - `backups/`
   - `private/`
   - `__pycache__` and similar.
4. If an external API key is introduced, support it as an optional environment variable with a clearly scoped name. Document rotation, expiration, and revocation procedure.
5. Do not echo secrets in error messages, health checks, frontend console, logs, or analytics events.
6. Sanitize logs by filtering patterns matching `api_key`, `password`, `token`, `secret`, `private`, `DATABASE_URL` query credentials, and URL credentials.

## Risk-limit configuration

Risk limits are configuration, not business logic constants. They must be:

- loaded from the settings object,
- persisted in a runtime setting row or seed file so they can be changed without redeployment,
- validated against sensible bounds (for example, `max_single_position_percent` between 0 and 100, `min_cash_percent` not exceeding 100 minus the largest position limit),
- used by deterministic risk services,
- never invented or overridden by the LLM.

The AI may explain whether a limit is breached, but it cannot change the configured limit or invent a new one. If no value is configured, fail or use a conservative default explicitly labeled as such.

## Data directories

Define root-relative paths. The application must create directories if they do not exist, with restrictive permissions where the OS supports it. The directories are:

- `DATA_DIR` — top-level local data.
- `DOCUMENTS_DIR` — original downloaded or imported EGX documents.
- `IMPORTS_DIR` — drop zone for manual CSV/JSON imports.
- `BACKUPS_DIR` — local backup output.
- Logs live under `LOG_DIR` or stdout; never write unrestricted credentials into log files.

## Logging configuration

- `LOG_LEVEL`: DEBUG, INFO, WARNING, ERROR.
- `LOG_FORMAT`: `json` for structured logs, `text` for local human-readable output.
- Logs must include correlation IDs, service name, timestamp (UTC), and safe context. They must not include the raw contents of documents, prompts, portfolio positions, or credentials.
- Access logs must strip query string tokens and credentials.
- Debug logging of provider responses should be opt-in and redacted.

## Provider-specific configuration

Each provider adapter declares its own typed configuration section. The settings object may expose provider-specific prefixes. Example:

```text
PUBLIC_WEB_PROVIDER_BASE_URL=
PUBLIC_WEB_PROVIDER_API_KEY=
PUBLIC_WEB_PROVIDER_RATE_LIMIT_PER_SECOND=1
PUBLIC_WEB_PROVIDER_TIMEOUT_SECONDS=30
PUBLIC_WEB_PROVIDER_RETRY_MAX_ATTEMPTS=3
PUBLIC_WEB_PROVIDER_RETRY_BACKOFF_SECONDS=2.0
```

A provider is not enabled simply because its variables are present; `MARKET_PROVIDER` selects the active adapter. Variables for inactive providers are validated but ignored unless selected.

## Validation and startup checks

At startup the application must:

1. Parse environment settings once and surface grouped validation errors.
2. Refuse to start if `AUTO_TRADING_ENABLED` is `true` in the MVP.
3. Refuse to start if `AUTH_ENABLED` is `true` unless authentication implementation is present.
4. Warn if `MARKET_PROVIDER=public_web` and the validation spike is not accepted.
5. Verify that directories are writable and paths are absolute or resolved from repo root.
6. Redact secrets when printing configuration for diagnostics.

## No automatic production defaults

Do not embed production-like URLs, cloud keys, default passwords, or sample account numbers in source code or committed example files. The committed `.env.example` uses `changeme`, `your-key-here`, or blank placeholders for every secret.

## Acceptance checklist

- [ ] A `.env.example` exists and is committed; `.env` is ignored.
- [ ] Backend uses one validated settings object for all environment access.
- [ ] Secrets are not read in frontend code, business logic, or provider parsing code.
- [ ] Logs and error responses redact credentials, document contents, and portfolio secrets.
- [ ] Risk limits, provider selection, model names, and freshness thresholds are configuration-driven.
- [ ] Startup validation fails fast on unsafe or incomplete configuration.
- [ ] `AUTO_TRADING_ENABLED` defaults to `false` and triggers a fatal error if `true` during MVP.
- [ ] Configuration changes do not require code edits unless schema changes are involved.
