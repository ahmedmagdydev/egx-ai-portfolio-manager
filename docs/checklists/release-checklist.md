# Release Readiness Checklist

Use this checklist before tagging the first release (`v0.1.0`) of the EGX AI Portfolio Manager. Every item must be checked, evidence must be provided, and the final sign-off must be completed before the release tag is pushed.

> **Scope reminder:** This release is local-first, decision-support only. It does not execute trades, provide personalized investment advice, or store data in the cloud.

---

## 1. Phase Completion

| # | Phase / Milestone | Status | Evidence / commit | Checked | Reviewer |
|---|-------------------|--------|-------------------|---------|----------|
| 1 | Milestone 0 — Environment ready | | | ☐ | |
| 2 | Milestone 1 — Portfolio engine + thin UI (Stage A) | | | ☐ | |
| 3 | Milestone 2 — Market, financial, technical data | | | ☐ | |
| 4 | Milestone 3 — Documents + RAG | | | ☐ | |
| 5 | Milestone 4 — AI assistant (analysis + risk) | | | ☐ | |
| 6 | Milestone 5 — AI chat | | | ☐ | |
| 7 | Milestone 6 — Backtesting + AI evaluation | | | ☐ | |
| 8 | Milestone 7 — Release readiness (this checklist) | | | ☐ | |

---

## 2. Functional Correctness

| # | Check | Evidence | Checked | Reviewer |
|---|-------|----------|---------|----------|
| 1 | Add a stock, add a BUY transaction, verify holdings. | | ☐ | |
| 2 | Add fees to a transaction and verify average cost and realized P&L. | | ☐ | |
| 3 | Add a SELL transaction and verify realized P&L. | | ☐ | |
| 4 | Delete a transaction and verify holdings revert. | | ☐ | |
| 5 | View portfolio allocation and sector allocation. | | ☐ | |
| 6 | Open a stock page and verify price, chart, financials, technicals. | | ☐ | |
| 7 | Run AI stock analysis and verify structured recommendation, confidence /100, reasons, risks, sources, `data_as_of`. | | ☐ | |
| 8 | Run AI portfolio analysis and verify whole-portfolio assessment. | | ☐ | |
| 9 | Open risk dashboard and verify breach flags, concentration, sector chart. | | ☐ | |
| 10 | Open AI chat and ask a portfolio question; verify streaming tool calls and Arabic/English response. | | ☐ | |
| 11 | Search documents and verify ranked results with citations. | | ☐ | |
| 12 | Run a backtest scenario and verify `as_of` filtering and metrics. | | ☐ | |
| 13 | Run AI evaluation harness and verify pass rate. | | ☐ | |

---

## 3. Safety and Compliance

| # | Check | Evidence | Checked | Reviewer |
|---|-------|----------|---------|----------|
| 1 | No endpoint, tool, or UI control can place a buy or sell order. | | ☐ | |
| 2 | Rebalancing suggestions are read-only and contain no order execution. | | ☐ | |
| 3 | AI system prompt refuses trade execution and guaranteed-return requests. | | ☐ | |
| 4 | Forbidden-phrase guard is active and tested. | | ☐ | |
| 5 | Confidence is displayed as `/100`, never as a probability of return. | | ☐ | |
| 6 | Every AI analysis and chat answer includes `data_as_of` and citations. | | ☐ | |
| 7 | Stale market data (>15 min) is flagged with a stale badge. | | ☐ | |
| 8 | Missing financial/disclosure data is surfaced, not fabricated. | | ☐ | |
| 9 | Investment disclaimer is shown on first launch and cannot be bypassed. | | ☐ | |
| 10 | AI limitation disclaimer is visible on analysis and chat pages. | | ☐ | |
| 11 | Data freshness and source information are visible on all price/ratio displays. | | ☐ | |
| 12 | Privacy notice explains what data stays local and what leaves the machine. | | ☐ | |

---

## 4. Security

| # | Check | Evidence | Checked | Reviewer |
|---|-------|----------|---------|----------|
| 1 | `.env` is in `.gitignore` and not committed. | | ☐ | |
| 2 | `.env.example` lists every environment variable with safe defaults. | | ☐ | |
| 3 | No API keys, database credentials, or secrets are in source code. | | ☐ | |
| 4 | Financial API keys (if any) are server-side only. | | ☐ | |
| 5 | CORS configuration restricts origins in development. | | ☐ | |
| 6 | All database queries use ORM/parameterized statements. | | ☐ | |
| 7 | File uploads (document ingestion) validate type, size, and storage path. | | ☐ | |
| 8 | Error responses do not expose stack traces or internal paths. | | ☐ | |
| 9 | Logs do not contain credentials, full document text, or PII. | | ☐ | |
| 10 | Dependencies are up to date; no known high-severity CVEs. | | ☐ | |

---

## 5. Arabic / RTL UX

| # | Check | Evidence | Checked | Reviewer |
|---|-------|----------|---------|----------|
| 1 | Arabic locale sets `dir="rtl"` and `lang="ar"` on `<html>`. | | ☐ | |
| 2 | Arabic font loads correctly across pages. | | ☐ | |
| 3 | All user-facing strings have Arabic translations or safe fallbacks. | | ☐ | |
| 4 | Currency displays as `ج.م` with correct numerals in Arabic mode. | | ☐ | |
| 5 | Dates display as `DD/MM/YYYY` in Arabic mode. | | ☐ | |
| 6 | Percentages display consistently (e.g., `٪` or `%`) in Arabic mode. | | ☐ | |
| 7 | Recommendation/risk badges render correctly in RTL. | | ☐ | |
| 8 | Price chart and sector allocation chart flip axes/legend in RTL. | | ☐ | |
| 9 | AI chat Arabic messages are right-aligned and input area flows RTL. | | ☐ | |
| 10 | Arabic text is proofread by a fluent speaker. | | ☐ | |
| 11 | Switching locale preserves page state and form data. | | ☐ | |

---

## 6. Performance and Reliability

| # | Check | Evidence | Checked | Reviewer |
|---|-------|----------|---------|----------|
| 1 | Docker Compose starts PostgreSQL, backend, and frontend on target hardware. | | ☐ | |
| 2 | Ollama `qwen3.5:9b` loads and responds within 10 seconds locally. | | ☐ | |
| 3 | Embedding model `qwen3-embedding:4b-q4_K_M` processes a batch in under 5 seconds. | | ☐ | |
| 4 | Dashboard first page load is under 3 seconds on localhost. | | ☐ | |
| 5 | AI chat first token appears within 10 seconds; no timeout under 30 seconds. | | ☐ | |
| 6 | Portfolio with 50 transactions renders without UI blocking. | | ☐ | |
| 7 | Backend handles 100 sequential quote requests without memory errors. | | ☐ | |
| 8 | GPU OOM falls back gracefully to CPU with a user warning. | | ☐ | |
| 9 | Application recovers from database disconnect and shows reconnect message. | | ☐ | |

---

## 7. Documentation

| # | Check | Evidence | Checked | Reviewer |
|---|-------|----------|---------|----------|
| 1 | `README.md` is complete and accurate. | | ☐ | |
| 2 | `README.ar.md` is complete and accurate. | | ☐ | |
| 3 | `docs/LOCAL_SETUP.md` walks a new developer through setup in under 60 minutes. | | ☐ | |
| 4 | `docs/USER_GUIDE.md` explains core features in English. | | ☐ | |
| 5 | `docs/USER_GUIDE.ar.md` explains core features in Arabic. | | ☐ | |
| 6 | `docs/TROUBLESHOOTING.md` covers Ollama, stale data, GPU OOM, database issues. | | ☐ | |
| 7 | `docs/HARDWARE.md` lists minimum and recommended specs. | | ☐ | |
| 8 | `docs/RELEASE_NOTES.md` is written for `v0.1.0`. | | ☐ | |
| 9 | API contracts are documented in `docs/api/` or generated from OpenAPI. | | ☐ | |
| 10 | Phase plans in `docs/phases/` are up to date with the released state. | | ☐ | |
| 11 | Decision log in `docs/decision-log.md` is current. | | ☐ | |

---

## 8. Testing

| # | Check | Evidence | Checked | Reviewer |
|---|-------|----------|---------|----------|
| 1 | Backend unit tests pass: `pytest backend/tests -q`. | | ☐ | |
| 2 | Frontend unit/component tests pass: `npm test`. | | ☐ | |
| 3 | E2E tests pass: `npm run test:e2e`. | | ☐ | |
| 4 | Portfolio calculation tests all pass. | | ☐ | |
| 5 | Financial ratio and technical indicator tests all pass. | | ☐ | |
| 6 | Risk engine tests all pass. | | ☐ | |
| 7 | RAG retrieval tests pass. | | ☐ | |
| 8 | Tool-calling integration tests pass. | | ☐ | |
| 9 | AI evaluation harness passes at ≥80%. | | ☐ | |
| 10 | Look-ahead bias test in backtest engine passes. | | ☐ | |
| 11 | Forbidden-phrase and safety tests pass. | | ☐ | |
| 12 | RTL visual regression tests pass. | | ☐ | |

---

## 9. Deployment and Packaging

| # | Check | Evidence | Checked | Reviewer |
|---|-------|----------|---------|----------|
| 1 | `docker-compose.yml` is present and tested. | | ☐ | |
| 2 | `scripts/start-local.ps1` and `scripts/start-local.sh` exist and work. | | ☐ | |
| 3 | `scripts/seed-demo.ps1` and `scripts/seed-demo.sh` populate demo data. | | ☐ | |
| 4 | `.env.example` is sufficient for a fresh local install. | | ☐ | |
| 5 | `.gitignore` excludes `.env`, `__pycache__`, `node_modules`, data exports. | | ☐ | |
| 6 | Database migrations are committed and can run from scratch. | | ☐ | |
| 7 | Ollama model pull commands are documented. | | ☐ | |
| 8 | A clean clone + `docker compose up` reaches the dashboard. | | ☐ | |

---

## 10. Final Review and Tag

| # | Check | Evidence | Checked | Reviewer |
|---|-------|----------|---------|----------|
| 1 | All items above are checked. | | ☐ | |
| 2 | No release-blocking bugs remain in the issue tracker. | | ☐ | |
| 3 | Known limitations are documented in `docs/RELEASE_NOTES.md`. | | ☐ | |
| 4 | Release branch is merged into `main`. | | ☐ | |
| 5 | Git tag `v0.1.0` is created with annotated message. | | ☐ | |
| 6 | Tag is pushed to origin. | | ☐ | |
| 7 | Final sign-off completed below. | | ☐ | |

---

## Sign-Off

| Role | Name | Date | Signature / confirmation |
|------|------|------|--------------------------|
| Engineering lead | | | |
| AI / safety reviewer | | | |
| Frontend / RTL reviewer | | | |
| QA lead | | | |
| Product / compliance lead | | | |

---

## Release Command Reference

```bash
# Ensure main is up to date
git checkout main
git pull origin main

# Create annotated tag
git tag -a v0.1.0 -m "EGX AI Portfolio Manager v0.1.0 — local-first decision support assistant. Includes portfolio engine, market/financial/technical data, RAG, AI analysis, risk engine, chat, backtesting, and evaluation. Arabic/RTL support included."

# Push tag
git push origin v0.1.0
```

---

## Post-Release Notes

After release:

- Monitor the issue tracker for setup problems on fresh clones.
- Capture user feedback on Arabic UX and AI answer quality.
- Continue running the evaluation harness on every significant prompt or model change.
- Do not begin future enhancements (mobile, cloud, automated trading) until core stability and evaluation metrics are satisfactory.
