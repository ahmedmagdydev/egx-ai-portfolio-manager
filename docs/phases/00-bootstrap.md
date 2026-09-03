# Phase 00 — Local Bootstrap

## Objective
Establish a reproducible Windows development baseline for a local, single-user EGX decision-support application. Prove that FastAPI, Next.js, PostgreSQL with pgvector, and local Ollama can eventually interoperate, without implementing product features or requiring an external LLM API.

## Prerequisites
- Windows host matching or exceeding the guide target (16 GB RAM, RTX 3060 6 GB); administrator rights for installers.
- Git, Node.js LTS, Python 3.11+, Docker Desktop (WSL2 backend), NVIDIA driver/CUDA-compatible runtime, and Ollama.
- PowerShell; ports selected for frontend, API, PostgreSQL, and Ollama must be free.
- Internet is needed only to install dependencies/pull images and models. Runtime remains local.
- Source guide remains unchanged and is the authority when this runbook is ambiguous.

## Expected modules and artifacts
This phase is expected to produce, during implementation (not in this documentation task):
- `frontend/` Next.js + TypeScript shell.
- `backend/app/` FastAPI shell and `backend/tests/`.
- `docker/`, `docker-compose.yml`, `.env.example`, `.gitignore`, root `README.md`.
- PostgreSQL database with the `vector` extension enabled; migration tooling and an initial empty migration.
- Local data roots: `data/raw/`, `data/processed/`, `data/documents/`.
- Health/readiness contracts and repeatable PowerShell setup/start/test instructions.
- Dependency lockfiles; no secrets, credentials, portfolio exports, model blobs, or generated data committed.

## Schema/API changes
- Database only: enable `vector`; reserve UTF-8 encoding and UTC timestamps. Do not create business tables yet.
- `GET /health/live`: process is running; no dependency checks.
- `GET /health/ready`: reports database and required extension state. Keep Ollama readiness separate so phases 01–05 can run without an LLM.
- Structured response shape: `status`, `service`, `version`, `checks`, `timestamp` (ISO-8601 UTC). Dependency failures return a non-2xx readiness status and a safe diagnostic code, never credentials.

## Ordered tasks
1. Record exact supported versions and verify `git --version`, `node --version`, `npm --version`, `python --version`, `docker version`, `nvidia-smi`, and `ollama --version` in PowerShell.
2. Establish the repository layout from the guide. Configure UTF-8 throughout so Arabic names, documents, prompts, logs, JSON, and database values round-trip unchanged.
3. Initialize the Python/FastAPI and Next.js/TypeScript shells with pinned dependencies. Add formatter, lint, type-check, test, and build commands.
4. Define environment-variable names and safe local defaults in `.env.example`; ensure real `.env` files and private data are ignored.
5. Define Docker Compose for PostgreSQL + pgvector with a named volume, health check, localhost-only exposure, and deterministic initialization/migrations.
6. Add liveness/readiness endpoints and database connection lifecycle. Confirm clean shutdown and restart preserve the local volume.
7. Pull `qwen3.5:9b` and `qwen3-embedding:4b-q4_K_M`; verify local generation and embedding manually. Do not couple application startup to either model yet.
8. Document one-command or short-command local workflows for install, migrate, start, test, stop, and reset. Reset must clearly warn that it destroys local data.
9. Run baseline lint, type checks, unit tests, frontend build, and a clean-machine-style restart check.

## Algorithms and edge cases
- Health checks use bounded timeouts and report each dependency independently; liveness must not fail merely because PostgreSQL is down.
- Normalize storage and transport timestamps to UTC while permitting later display in local time.
- Preserve Arabic text in NFC Unicode; never transliterate or ASCII-strip it. Verify right-to-left content survives JSON and PostgreSQL.
- Bind services to loopback for a single-user machine. A port collision must produce an actionable message rather than silently choosing a different endpoint.
- Docker unavailable, virtualization disabled, GPU driver mismatch, insufficient disk/RAM, model pull interruption, and Ollama CPU fallback must have documented recovery paths.
- PostgreSQL initialization and migrations must be idempotent. Concurrent startup must not apply a migration twice.

## Tests
- Backend smoke test for liveness; readiness success with PostgreSQL and failure with it stopped.
- Migration test on an empty database and repeat migration with no change; assert `vector` extension exists.
- UTF-8 round-trip fixture containing Arabic and English text through API serialization and PostgreSQL.
- Frontend type-check/build and a smoke request to the API health endpoint using a configurable base URL.
- Secret hygiene check: ignored `.env`, no credentials in logs, and `.env.example` contains placeholders only.
- Mock external boundaries; bootstrap CI/tests must not download models, call public sites, or require Ollama/GPU. Mark real Ollama checks as opt-in local integration tests.

## Manual demo
1. From a fresh PowerShell session, copy `.env.example` to the local ignored environment file and start PostgreSQL, backend, and frontend using documented commands.
2. Open liveness and readiness endpoints and show PostgreSQL/pgvector healthy.
3. Submit/store/read an Arabic-English probe string and show exact preservation.
4. Run `ollama run qwen3.5:9b` and ask for a concise explanation of portfolio diversification in Arabic and English.
5. Generate one embedding with the configured embedding model, then disconnect the network and repeat local health/model checks.
6. Restart the stack and prove database persistence; stop PostgreSQL and show graceful readiness degradation.

## Observability and failure handling
- Structured local logs include timestamp, level, service, request/correlation ID, route, duration, and safe error code.
- Log startup versions and dependency state, but never prompts containing private portfolio data, credentials, connection strings, or API keys by default.
- Health timeouts, migration errors, unavailable database, and model absence must fail explicitly with remediation hints.
- Docker/PostgreSQL logs remain locally inspectable; use bounded retention where configured.

## Acceptance checklist
- [ ] Supported Windows prerequisites and exact versions are documented and verified.
- [ ] Repository shells start locally and all baseline checks pass.
- [ ] PostgreSQL persists data and has pgvector enabled through an idempotent migration.
- [ ] Arabic/English UTF-8 round-trip succeeds.
- [ ] Liveness and readiness behave correctly under dependency failure.
- [ ] Qwen 9B responds locally and the embedding model returns a vector.
- [ ] Automated tests use mocks and require neither public services nor model downloads.
- [ ] No external LLM API, cloud deployment, product feature, or secret is introduced.
- [ ] Setup, reset, troubleshooting, and safe teardown are reproducible.

## Dependencies
- Upstream: source guide and approved phase plan only.
- Enables: every later phase.
- Ollama verification here is environmental only; application integration belongs to phase 06.
