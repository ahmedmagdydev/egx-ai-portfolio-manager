# 04 — Local Environment

## Purpose and boundaries

This runbook prepares the supported Windows development environment for a local, single-user EGX decision-support application. It does not provision cloud services, authentication, brokerage connectivity, or automated trading. Technical interfaces and diagnostics are English; future user-facing screens and assistant output must support Arabic and right-to-left (RTL) rendering.

## Target machine

The baseline is Windows 10/11, 16 GB RAM, Intel i7-11800H, NVIDIA RTX 3060 Laptop GPU (6 GB VRAM), and sufficient SSD space for Docker images, PostgreSQL data, source documents, and Ollama models. Keep at least 25 GB free before bootstrap. The design must remain usable without an external LLM API.

## Required software

Install and record exact versions in the future lockfiles/tool-version files:

1. Git.
2. Node.js LTS and Corepack; use the package manager selected by the technology decision record.
3. Python 3.11 or the later compatible version selected by the project, including `venv`.
4. Docker Desktop with the WSL 2 backend and Docker Compose v2.
5. Current NVIDIA Windows driver appropriate for the GPU.
6. Ollama for Windows.
7. Optional PostgreSQL client (`psql`). PostgreSQL itself should run in Docker unless an ADR changes this.

Do not install project dependencies globally. Future backend dependencies belong in a virtual environment; frontend dependencies belong in the workspace package store.

## Windows setup sequence

### 1. Verify virtualization and Docker

Enable hardware virtualization and WSL 2, install Docker Desktop, select the WSL 2 engine, and cap Docker resources so Ollama can run concurrently. A starting budget is 4 CPUs and 6 GB RAM for Docker; tune based on measured use. Verify:

```powershell
docker version
docker compose version
docker run --rm hello-world
```

Expected: client and server respond, Compose reports v2, and the smoke-test container exits successfully. If the Docker daemon is unavailable, start Docker Desktop. If WSL integration fails, update WSL and reboot before changing application settings.

### 2. Verify language toolchains

```powershell
git --version
node --version
corepack --version
python --version
python -m venv --help
```

The future bootstrap phase must pin supported versions. A machine is not accepted merely because commands exist: their versions must satisfy those pins.

### 3. Verify NVIDIA support

```powershell
nvidia-smi
```

Expected: the RTX 3060 is listed without driver errors. Ollama may fall back to CPU, but this must be visible in diagnostics because latency and memory behavior differ. Do not install CUDA toolkits unless an implementation dependency explicitly requires one.

### 4. Install and verify Ollama

```powershell
ollama --version
ollama serve
```

Only start `ollama serve` manually when the Windows service is not already listening; avoid duplicate servers. The default local endpoint is `http://127.0.0.1:11434`. It must not be exposed to the LAN.

Install the guide’s initial models:

```powershell
ollama pull qwen3.5:9b
ollama pull qwen3-embedding:4b-q4_K_M
ollama list
ollama run qwen3.5:9b
```

Use the interactive prompt `Analyze the concept of portfolio diversification in Arabic and English.` Confirm readable English and Arabic output, then exit. During implementation, verify embeddings through the Ollama API using non-sensitive sample text. Model names are configurable because availability may change; changing them requires compatibility and evaluation checks.

## Intended local topology

| Service | Default binding | Purpose | Exposure rule |
|---|---:|---|---|
| Next.js | `127.0.0.1:3000` | Arabic-capable UI | loopback only |
| FastAPI | `127.0.0.1:8000` | versioned application API | loopback only |
| PostgreSQL/pgvector | container-only or `127.0.0.1:5432` | durable data | never public |
| Ollama | `127.0.0.1:11434` | generation and embeddings | never public |

Port changes belong in local environment variables. Health probes must use configured URLs rather than hard-coded ports.

## Environment preparation

When scaffolding exists:

1. Clone/open the repository on a local SSD.
2. Copy the documented example environment file to the ignored local environment file; never populate or commit real values in the example.
3. Create the Python virtual environment and install locked dependencies.
4. Enable the pinned frontend package manager and install from its lockfile.
5. Start PostgreSQL/pgvector through the project Compose file.
6. Apply migrations, then load synthetic/demo seed data only.
7. Start backend, frontend, and Ollama.

Variable names, precedence, validation, and secret handling are specified in [05 — Configuration and Secrets](05-configuration-and-secrets.md). This document intentionally does not create `.env` or Compose files.

## Required health checks

The implemented system must provide:

- API liveness: process/event loop works without checking dependencies.
- API readiness: database reachable, migrations current, required extensions present; Ollama/provider status reported separately so deterministic portfolio functions can remain available during degradation.
- Database: `SELECT 1`, migration revision, and `vector` extension check.
- Ollama: endpoint reachable, configured generation and embedding models installed.
- Frontend: page loads, API base URL resolves, Arabic sample text renders RTL.
- Market provider: disabled/mock/live-validation status plus last successful fetch; live failure must not make historical portfolio records unavailable.

Health responses must not reveal credentials, private paths, portfolio values, raw prompts, or document contents.

## Troubleshooting

| Symptom | Checks | Safe action |
|---|---|---|
| Port in use | identify owning process; compare configured ports | stop the duplicate or select an unused loopback port |
| Docker cannot start | virtualization, WSL status, free memory/disk | update WSL, restart Docker, reclaim unused images cautiously |
| `pgvector` missing | image tag and extension migration | use the approved pgvector image; do not manually patch production-like data |
| Ollama is slow/out of memory | `nvidia-smi`, model residency, context, concurrent requests | serialize requests, reduce context/batch, unload the other model; do not silently switch models |
| Model not found | `ollama list`, configured exact tag | pull the approved tag and rerun evaluation after any substitution |
| Backend cannot reach host Ollama from container | host gateway URL and firewall | use documented Docker host gateway; retain loopback/LAN restrictions |
| Arabic is disconnected or left-to-right | UTF-8, font, `dir="rtl"`, browser | fix presentation; never reshape or transliterate stored source text destructively |
| Database data disappears | volume configuration | stop writes, inspect volumes, restore from verified backup |
| Public source rejects requests | provider logs/status | stop retries, honor backoff/terms, use mocks or manual import; never bypass controls |

## Resource discipline

Run one generation at a time initially. Avoid loading generation and embedding models concurrently unless measurements show headroom. Bound context length, document size, embedding batch size, database pool size, and ingestion concurrency. Every long operation needs timeout and cancellation. Capture peak RAM/VRAM, latency, and disk growth during release checks.

## Phase 0 acceptance checklist

- [ ] Supported Windows, Git, Node, Python, Docker Compose, NVIDIA driver, and Ollama versions are recorded and pass checks.
- [ ] Docker runs a disposable container and the future PostgreSQL/pgvector service becomes ready.
- [ ] Qwen generation responds locally in English and Arabic.
- [ ] The configured embedding model produces an embedding of the expected dimension.
- [ ] No external LLM API is necessary for basic operation.
- [ ] All service listeners are local-only and no credential is present in frontend-visible configuration.
- [ ] Liveness/readiness distinguish mandatory deterministic dependencies from optional/degraded AI and live-data dependencies.
- [ ] Arabic text renders correctly in an RTL smoke test.
- [ ] Mock/fixture mode works with networking disabled.
- [ ] Resource use fits the 16 GB RAM/6 GB VRAM target without sustained swapping or crashes.
