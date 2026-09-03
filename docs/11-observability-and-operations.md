# 11 — Observability and Operations

## Purpose

This document defines how the local application is observed, audited, diagnosed, backed up, and kept healthy within the resource constraints of the target hardware.

## Logging philosophy

1. Logs are structured, human-readable locally, and never contain secrets or private portfolio data.
2. Every request carries a `request_id` correlation ID that threads through backend logs.
3. Logs include UTC timestamp, log level, service name, operation, duration, safe context, and result code.
4. DEBUG logs may include sanitized metadata but never raw documents, prompts, or credentials.
5. Access logs omit query strings and bodies that may contain secrets.

## Structured logging fields

Standard fields for each event:

- `timestamp` — UTC ISO-8601.
- `level` — DEBUG, INFO, WARNING, ERROR, CRITICAL.
- `logger` — module path.
- `request_id` — correlation ID.
- `event` — stable event name (e.g., `market_data.fetch`, `llm.generate`, `portfolio.transaction.create`).
- `duration_ms` — where applicable.
- `symbol` — where applicable.
- `provider` or `model` — where applicable.
- `status` — `ok`, `stale`, `error`, `degraded`.
- `error_code` — typed safe error code.
- `context` — small safe JSON object; excludes secrets, balances, document text, and raw prompts.

## Audit trail

Record a durable audit trail for:

- market data fetch: provider, symbol, range, market timestamp, fetched at, freshness, record count, latency, retry count;
- transaction changes: transaction type, symbol, quantity, price, fees, timestamp, resulting cash and holding state;
- LLM requests: model name, token budget, tool calls executed, duration, status, not the raw prompt text or user document content;
- document ingestion: source, checksum, document type, language, published at, chunk count;
- analysis generation: type, symbols, data_as_of, sources used, missing_information, status.

Audit records are stored in PostgreSQL or an append-only local log. They are not exported unless the user explicitly configures local export.

## Health and readiness checks

See [04 — Local Environment](04-local-environment.md). The `/api/v1/health/*` endpoints must return:

- `live` — process is alive;
- `ready` — database reachable, migrations current, `pgvector` present;
- `ollama` — endpoint reachable, configured models installed;
- `providers` — status and last successful refresh for each provider.

A degraded optional dependency (Ollama, public market source) must not make the portfolio API unavailable.

## Metrics

Maintain lightweight local metrics in logs or a small in-app metrics store:

- request latency and count by endpoint;
- market provider success/stale/failure rate;
- Ollama generation/embedding latency and token counts if available;
- transaction throughput;
- document ingestion count and chunk count;
- RAG retrieval latency and result count.

No external metrics SaaS is required in the MVP. Metrics should be queryable from logs or a local endpoint.

## Local backup and restore

### Backup

1. Stop or quiesce writes before backup.
2. Run `pg_dump` into `BACKUPS_DIR` with filename `egx_portfolio_YYYYMMDD_HHMMSS.sql.gz`.
3. Include `data/documents` and `data/imports` in a separate archive.
4. Verify backup integrity with a test restore on a throwaway database before relying on it.
5. Keep at least the last three verified backups and prune older ones manually.

### Restore

1. Create a new local database.
2. Restore the SQL dump.
3. Verify migration version matches codebase.
4. Restore document archives to the configured `DOCUMENTS_DIR`.
5. Run health checks and a small portfolio reconciliation before declaring success.

## Failure recovery

| Scenario | Response |
|---|---|
| Database unavailable | API returns 503; UI shows degraded message; portfolio reads fail gracefully. |
| Ollama unavailable | AI endpoints return unavailable; deterministic endpoints continue. |
| Market provider down | Last cached data is served as `stale`; no new data is invented. |
| Provider returns bad data | Bad records are quarantined; existing validated data is preserved. |
| Disk full | Stop ingestion and alert; do not overwrite backups or documents. |
| Model returns malformed analysis | Post-processor fails safe and returns an error; do not present unvalidated JSON. |
| Import file invalid | Reject file with row-level error report; do not partially commit. |

## Resource constraints

The target machine is 16 GB RAM, 6 GB VRAM, and an 8-core CPU. Operations must:

1. Run only one LLM generation at a time by default.
2. Avoid loading the generation and embedding models concurrently unless measurements prove headroom.
3. Limit embedding batch size, context length, database pool, and ingestion concurrency.
4. Use streaming only when it reduces memory.
5. Periodically measure peak RAM, VRAM, and disk use during long operations and capture in release notes.

## Security and privacy operations

1. Services bind to loopback only.
2. No remote access is enabled by default.
3. Backups are stored locally and encrypted where the OS supports it.
4. Documents are not transmitted to external services unless explicitly configured and audited.
5. Audit logs are retained locally and rotated to avoid disk exhaustion.

## Maintenance commands

Provide scripts in `scripts/operations/` for:

- `health.ps1` / `health.py` — check all local services.
- `backup.py` — database and document backup.
- `restore.py` — verified restore.
- `cleanup.py` — prune old logs, quarantined records, and temporary imports.
- `diagnose.py` — collect safe diagnostics (versions, health, disk, memory, provider status) without leaking secrets.

## Alerting

For a local single-user MVP, alerting is primarily in-UI and in logs. A task tray or lightweight desktop notification may indicate:

- stale market data exceeding the freshness threshold;
- Ollama not reachable;
- failed provider refresh;
- disk space low;
- backup completed or failed.

## Operations runbook

1. Start Docker Desktop.
2. Start PostgreSQL/pgvector container.
3. Start Ollama service.
4. Start FastAPI backend.
5. Start Next.js frontend.
6. Run health checks.
7. Verify mock data is available.
8. Optionally run a manual public-source refresh if validation is accepted.

For shutdown, stop frontend, backend, and then container services. Ollama may remain running but should be unloaded if memory is needed.

## Acceptance checklist

- [ ] Structured logging is implemented with correlation IDs.
- [ ] Secrets, document contents, and raw prompts are never logged.
- [ ] Audit trail captures data source, timestamp, API request, LLM request, tool calls, and errors.
- [ ] Health endpoints distinguish live, ready, Ollama, and provider status.
- [ ] Backup and restore procedure is documented and tested.
- [ ] Failure scenarios have safe, documented responses.
- [ ] Resource limits respect 16 GB RAM and 6 GB VRAM.
- [ ] Operations scripts exist for health, backup, restore, cleanup, and diagnostics.
- [ ] No external operation or cloud service is required in the MVP.
