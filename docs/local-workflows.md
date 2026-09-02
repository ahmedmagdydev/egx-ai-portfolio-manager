# Local workflows

All commands below run from the repository root on Linux.

## Install

```bash
make install
```

This creates `backend/.venv`, installs pinned dependencies, writes the generated Python lock file, copies `.env.example` to `.env` if absent, and installs the committed frontend lockfile with `npm ci`.

## Migrate and start

```bash
make db-up
make migrate
make backend    # terminal 1
make frontend   # terminal 2
```

PostgreSQL is bound to `127.0.0.1`. Verify liveness and readiness with `curl http://127.0.0.1:8000/health/live` and `curl http://127.0.0.1:8000/health/ready`. Ollama is checked separately at `/health/ollama`; its failure does not make `/health/ready` fail.

## Test and stop

```bash
make lint
make typecheck
make test
make test-integration
make build
make stop
make db-down
```

`test-integration` needs the running database. `make db-down` removes the container while preserving the named volume, so restarting and migrating does not lose the extension or future local data.

## Reset

```bash
CONFIRM=yes make reset
```

Reset is destructive: it removes the PostgreSQL container and named volume. Without `CONFIRM=yes`, the target refuses to run.

## Troubleshooting

- **Docker unavailable:** start Docker Engine, then rerun `make db-up`; alternatively provide a local PostgreSQL and update `.env`.
- **Port collision:** inspect listeners with `ss -ltnp`, stop the conflicting process, or change `POSTGRES_PORT`, `API_PORT`, or `FRONTEND_PORT` in the ignored `.env`. Keep the frontend API URL aligned.
- **Migration fails:** confirm `.env` credentials match Compose, wait for `docker compose ps` to show `healthy`, and rerun `make migrate`.
- **Model pull interruption:** retry the pull when Ollama is available. No bootstrap test downloads models.
- **Ollama CPU fallback:** Ollama can run without a GPU at reduced speed; leave model health degraded until the configured models are available.
- **Arabic output looks escaped:** use a UTF-8 terminal and inspect raw response bytes; the API JSON response is configured with `ensure_ascii=False`.

PowerShell users can use `Copy-Item .env.example .env`, `docker compose up -d postgres`, `python -m alembic -c backend/alembic.ini upgrade head`, and equivalent `npm`/`uvicorn` commands. The maintained workflow and `Makefile` target Linux.
