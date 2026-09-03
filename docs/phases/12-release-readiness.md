# Phase 12 — Release Readiness

> **Goal:** Prepare the application for safe, local personal use as an AI investment decision-support tool. Ensure documentation, security, privacy, performance, and legal disclaimers are in place before the first release.  
> **RTL/Arabic requirement:** All user-facing release assets (README, onboarding, disclaimers) must have Arabic versions or Arabic-safe fallbacks; the Arabic UI must be fully RTL and numerically localized.

---

## 1. Prerequisites

| Prerequisite | Evidence required |
|--------------|-------------------|
| Phase 09 (Dashboard) Stage A complete | Thin portfolio UI is stable and manually demonstrated. |
| Phase 09 (Dashboard) Stage B complete | Full dashboard, stock pages, analysis, risk, documents pages are functional. |
| Phase 10 (AI Chat) complete | Chat assistant streams tool calls and answers in Arabic/English with citations. |
| Phase 11 (Backtesting and Evaluation) complete | Baseline backtest and AI evaluation reports exist; safety/hallucination tests pass. |
| All previous phases signed off | Each phase definition-of-done checklist is complete. |
| Local end-to-end smoke test passed | User can add transaction → view holdings → ask AI → see risk → run backtest on one machine. |

---

## 2. Ordered Tasks

### 2.1 Finalize legal and investment disclaimers

Create and prominently display:

1. **Investment disclaimer (Arabic and English)** — appears on first launch, login, and AI chat/analysis pages.
2. **Data freshness disclaimer** — every price, ratio, and analysis shows `data_as_of`.
3. **AI limitation disclaimer** — AI provides analysis, not investment advice; it does not execute trades.
4. **Privacy notice** — data is local-first; explain what is stored locally and what leaves the machine.

English sample:

> "This tool is for educational and decision-support purposes only. It does not provide personalized investment advice, guarantee returns, or execute trades. Always verify data timestamps and consult a licensed financial advisor before making investment decisions."

Arabic sample:

> "هذه الأداة للأغراض التعليمية ودعم اتخاذ القرار فقط. لا تقدم نصائج استثمارية مخصصة، ولا تضمن عوائد، ولا تنفذ صفقات. تحقق دائمًا من تواريخ البيانات واستشر مستشارًا ماليًا مرخصًا قبل اتخاذ قرارات الاستثمار."

**Exit gate 2.1:** Disclaimers are reviewed and stored in `frontend/lib/legal/`; first-launch modal cannot be bypassed without acknowledgment.

### 2.2 Complete user documentation

Create:

- `README.md` (English)
- `README.ar.md` (Arabic)
- `docs/LOCAL_SETUP.md` — step-by-step local installation on Windows with WSL/Docker.
- `docs/USER_GUIDE.md` — how to add a transaction, read the dashboard, use AI chat, understand risk, run backtests.
- `docs/USER_GUIDE.ar.md` — Arabic version.
- `docs/TROUBLESHOOTING.md` — common failures: Ollama not running, stale data, GPU out of memory, model download.

**Exit gate 2.2:** A new developer can set up the project from `LOCAL_SETUP.md` in under 60 minutes.

### 2.3 Finalize repository structure

Ensure the repository matches the recommended structure from the implementation guide:

```text
egx-ai-portfolio/
├── frontend/
├── backend/
├── data/
│   ├── raw/
│   ├── processed/
│   └── documents/
├── docker/
├── scripts/
├── docs/
├── docker-compose.yml
├── .env.example
├── .gitignore
└── README.md
```

**Exit gate 2.3:** Directory tree matches; no secrets committed.

### 2.4 Environment and secrets hardening

- Confirm `.env` is in `.gitignore`.
- Provide `.env.example` with all keys and safe defaults.
- Document that no financial API keys are exposed in the frontend.
- If optional external LLM fallback is configured, the key must be server-side only.
- Rotate any keys used during development before release.

**Exit gate 2.4:** `git ls-files | grep -E '\.env|secret|key'` returns only `.env.example` and documentation references.

### 2.5 Performance and resource validation

Target machine: 16 GB RAM, Intel i7-11800H, RTX 3060 Laptop 6 GB VRAM.

Validate:

- Ollama `qwen3.5:9b` loads and responds within 10 seconds for typical prompts.
- Embedding model `qwen3-embedding:4b-q4_K_M` completes a batch of 10 chunks within 5 seconds.
- Dashboard first page load is under 3 seconds on localhost.
- AI chat first token appears within 10 seconds; full answer streams without timeout.
- Portfolio with 50 transactions renders without blocking the UI.
- Docker Compose stack starts all services without memory errors.

Document minimum and recommended hardware in `docs/HARDWARE.md`.

**Exit gate 2.5:** Performance report stored in `docs/perf/release-validation.md`.

### 2.6 Logging and audit readiness

- Application logs: data source, timestamp, API requests, LLM requests, tool calls, errors.
- Audit log: AI analysis and chat outputs with sources, but no credentials or full document text.
- Log retention: 30 days locally; document rotation policy.
- Error reporting: user sees friendly message; full stack trace goes to server log only.

**Exit gate 2.6:** Log samples reviewed; no PII, credentials, or full portfolio exports in logs.

### 2.7 Final test suite run

Run all automated tests:

```bash
# Backend
pytest backend/tests -q

# Frontend unit/component
npm run test

# E2E / visual regression
npm run test:e2e
```

Expected results:

- Unit tests: ≥90% pass rate for core engine; all portfolio/risk/financial/technical tests pass.
- E2E: add transaction, view dashboard, AI analysis, chat, risk dashboard, document search flows pass.
- AI evaluation: ≥80% pass rate on fixed dataset.
- Visual regression: no unintended RTL/LTR layout changes.

**Exit gate 2.7:** Test report saved in `docs/qa/final-test-report.md`; no release-blocking failures.

### 2.8 Packaging and local deployment

Create:

- `docker-compose.yml` for local orchestration (frontend dev, backend, PostgreSQL + pgvector, optional Ollama).
- `scripts/start-local.ps1` and `scripts/start-local.sh` to simplify startup.
- `scripts/seed-demo.ps1` / `seed-demo.sh` to populate a demo portfolio and market data.

**Exit gate 2.8:** A fresh clone runs with `docker compose up` or the provided start script and reaches the login/dashboard.

### 2.9 Final security review

Checklist:

- [ ] No secrets in repository.
- [ ] `.env.example` covers all environment variables.
- [ ] CORS allows only localhost in development.
- [ ] No SQL injection vectors (use ORM/parameterized queries).
- [ ] No arbitrary file upload paths.
- [ ] Document ingestion validates file type and size.
- [ ] AI system prompt includes refusal for trade execution and guaranteed-return claims.
- [ ] Input validation on all API endpoints.
- [ ] Error responses do not leak stack traces or internal paths.

**Exit gate 2.9:** Security review signed off in `docs/qa/security-review.md`.

### 2.10 Arabic/RTL final review

Checklist:

- [ ] All Arabic labels proofread by a fluent speaker.
- [ ] `dir="rtl"` applied to `<html>` and main containers in Arabic locale.
- [ ] Recommendation badges, risk badges, and AI analysis cards render correctly in RTL.
- [ ] Charts (price, sector allocation, evaluation charts) flip axes/legend for RTL.
- [ ] Date formatting: `DD/MM/YYYY` for Arabic.
- [ ] Currency formatting: `ج.م` prefix with correct numerals.
- [ ] Chat interface supports Arabic input and right-aligned bubbles.
- [ ] Disclaimers available in Arabic.

**Exit gate 2.10:** RTL review signed off in `docs/qa/rtl-review.md`.

### 2.11 Create release notes and version tag

Create `docs/RELEASE_NOTES.md` with:

- Version number (e.g., `v0.1.0`).
- Scope summary.
- Known limitations.
- Supported hardware.
- Required models and download commands.
- Link to setup guide.
- Link to backtest/evaluation baseline report.

Tag the repository:

```bash
git tag -a v0.1.0 -m "Initial local release: portfolio, AI analysis, chat, risk, backtesting."
```

**Exit gate 2.11:** Tag pushed; release notes merged to main branch.

---

## 3. Artifacts

| Artifact | Location | Purpose |
|----------|----------|---------|
| Disclaimers | `frontend/lib/legal/` and UI modals | Legal and safety notices. |
| README | `README.md`, `README.ar.md` | Project overview. |
| Local setup guide | `docs/LOCAL_SETUP.md` | Developer onboarding. |
| User guide | `docs/USER_GUIDE.md`, `docs/USER_GUIDE.ar.md` | End-user instructions. |
| Troubleshooting guide | `docs/TROUBLESHOOTING.md` | Common issues. |
| Hardware guide | `docs/HARDWARE.md` | Minimum/recommended specs. |
| Performance report | `docs/perf/release-validation.md` | Resource validation. |
| QA test report | `docs/qa/final-test-report.md` | Final test results. |
| Security review | `docs/qa/security-review.md` | Security checklist sign-off. |
| RTL review | `docs/qa/rtl-review.md` | Arabic/RTL sign-off. |
| Release notes | `docs/RELEASE_NOTES.md` | Version summary. |
| Docker Compose | `docker-compose.yml` | Local deployment. |
| Start scripts | `scripts/start-local.*` | Simplified startup. |
| Demo seed scripts | `scripts/seed-demo.*` | Demo data. |
| Git tag | `v0.1.0` | Version marker. |

---

## 4. Tests and Manual Demos

### Final smoke test

Run the complete user journey:

1. Fresh clone → run `scripts/start-local.ps1` or `docker compose up`.
2. Acknowledge disclaimers.
3. Add `COMI` holding (BUY 100 @ 90.00 EGP).
4. Add `FWRY` holding (BUY 50 @ 30.00 EGP).
5. View `/portfolio` → verify summary and sector allocation.
6. Open `/stocks/COMI` → verify price, chart, financials, technicals.
7. Click AI analysis → verify recommendation, confidence /100, sources, `data_as_of`.
8. Open `/risk` → verify no critical breaches or correct breach messages.
9. Open `/chat` → ask "ما أكبر 3 مخاطر في محفظتي؟" → verify Arabic response with citations.
10. Open `/documents` → search "إيرادات COMI" → verify results with source and date.
11. Switch to English → verify LTR and English formatting.
12. Shut down and restart → verify data persists in PostgreSQL.

### Release checklist manual verification

Use `docs/checklists/release-checklist.md` and sign each item.

---

## 5. Safety and Failure Behavior

| Scenario | Expected behavior |
|----------|-------------------|
| User bypasses disclaimer | Cannot access main UI until acknowledged; preference stored locally. |
| Ollama not installed on first run | Setup wizard links to Ollama download and model pull commands. |
| GPU out of memory | Graceful fallback to CPU for Ollama; warn user about slower responses. |
| Database not reachable | Show connection error; provide link to `TROUBLESHOOTING.md`. |
| Stale data on release day | Show amber stale badge; do not block launch. |
| AI evaluation pass rate <80% | Block release until failing categories are fixed or scoped out with documented limitation. |
| Secret leak detected in final review | Remove secret, rotate it, and re-tag release. |
| Test failure on final run | Triage as release-blocker or documented known issue. |

---

## 6. Exit Gates

This phase is complete only when:

1. All previous phase exit gates are satisfied.
2. Disclaimers are displayed and acknowledged before first use.
3. README, user guide, troubleshooting, and Arabic documentation are complete.
4. `.env.example` is complete; no secrets are committed.
5. Performance and resource requirements are validated on target hardware.
6. Final test suite passes with no release-blocking failures.
7. Security and RTL reviews are signed off.
8. Docker/local deployment works from a fresh clone.
9. Release notes are written and a version tag is created.
10. The `docs/checklists/release-checklist.md` is fully checked and signed by the reviewer.

---

## 7. Post-Release Notes

After the initial local release, the project enters maintenance and incremental improvement. Future work (not part of this release) may include:

- Daily portfolio briefing.
- Earnings and dividend calendars.
- Watchlists and price alerts.
- Fundamental/technical screening.
- Scenario analysis and Monte Carlo simulation.
- Optional external LLM fallback.
- Mobile application.
- Cloud deployment.

These items must remain out of scope until the core architecture and evaluation metrics are stable.
