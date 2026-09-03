# Phase 06 — Ollama and Tools

## Objective
Integrate local Qwen through an isolated `LLMProvider` and expose narrowly typed tools for portfolio, market, financial, technical, and document facts. The model reasons over verified/retrieved/calculated context, cites evidence, supports Arabic and English, and never becomes the numerical source of truth or executes trades.

## Prerequisites
- Phases 00–05 accepted and their APIs/services return provenance, timestamps, freshness, warnings, and deterministic values.
- Local Ollama runs `qwen3.5:9b`; host capacity and timeout/concurrency limits are documented. No external LLM API is required.
- Tool-calling format supported by the pinned Ollama/model versions has been verified. A scripted `FakeLLMProvider` is available for deterministic tests.
- Investment safety/system rules from the guide are approved in Arabic/English behavior: decision support only, no certainty, no automatic orders, insufficient evidence stated explicitly.

## Expected modules and artifacts
- `backend/app/ai/`: `LLMProvider`, Ollama adapter, message/tool/result schemas, orchestrator, system prompt/version, bounded conversation/context handling.
- `backend/app/tools/`: typed registry, authorization/policy layer, adapters calling domain services, argument/result serializers, and audit events.
- Initial tools: `get_portfolio`, `get_position`, `get_quote`, `get_historical_prices`, `get_financial_snapshot`, `get_technical_indicators`, `search_documents`, `get_latest_news`, `calculate_portfolio_allocation`, `calculate_sector_allocation`; `calculate_portfolio_risk` remains unavailable until a later risk phase or returns explicitly unsupported.
- Analysis/chat API contract, bilingual fixed evaluation set, fake provider/tool fixtures, integration tests, prompt/tool version manifest, and local performance baseline.

## Schema/API changes
No required business-table changes. If local conversation persistence is approved, store minimal single-user message/audit data with retention controls and no secrets; otherwise keep it in memory. Tool-call logs store IDs, tool name/version, timing/status and redacted arguments/results—not full private portfolio content by default.

Provider contract follows `generate(messages, tools=None)` and returns typed assistant text, zero or more tool calls, finish reason, model/version, and usage/timing when Ollama supplies it. Define errors for unavailable model/runtime, timeout, malformed response, invalid tool call, and context overflow.

Add an analysis endpoint (for example `POST /api/ai/analyze` or `/api/ai/chat`) accepting message, language preference/`auto`, optional symbol, and correlation/conversation ID. Response distinguishes `verified_facts`, `calculated_metrics`, `retrieved_information`, `interpretation`, `assumptions`, `missing_information`, `warnings`, `data_as_of`, and `sources`. Recommendations may remain out of scope until Portfolio AI; no arbitrary unvalidated internal blob is trusted.

## Ordered tasks
1. Freeze provider, message, tool-call, citation, and response schemas independently of Ollama. Add scripted fake model responses before real integration.
2. Implement Ollama adapter against loopback with model allowlist, bounded connection/generation timeouts, one local generation at a time by default, cancellation, and clear model-not-installed diagnostics.
3. Write/version the system prompt: use tools for current/numeric facts; distinguish facts/calculations/retrieval/interpretation/assumptions; cite document source/date; report data time and stale/incomplete evidence; never promise returns or execute trades; resist instructions inside documents/tool results.
4. Implement a registry with JSON/Pydantic argument validation, output size limits, explicit read-only allowlist, recursion/round/tool-count budget, and stable serialization. The model cannot call arbitrary Python, shell, SQL, HTTP, file, or order functions.
5. Wrap accepted domain services. Tools return structured values plus source, timestamps, freshness, warnings, and missing fields; they do not format persuasive prose or ask the model to recalculate numbers.
6. Implement orchestration loop: send prompt/tools, validate requested calls, execute approved calls, append typed results, repeat within budget, and validate final response/citations. Use deterministic application routing for obvious symbol/portfolio context where helpful.
7. Handle Arabic, English, and mixed requests. Preserve EGX symbols and numeric precision; answer in requested/detected language while citations and company names retain originals.
8. Add fixed evaluations and fault injection. Measure local latency/memory/context size; tune context selection before changing model size.
9. Expose API with cancellation and safe errors; complete manual safety and offline-mode demonstrations.

## Algorithms and edge cases
- Tool arguments are untrusted model output: reject unknown tool/name, extra or invalid fields, malformed dates/symbols, excessive range/top-k, and repeated identical calls. Normalize symbols only through domain rules.
- At most a configured number of rounds/tool calls; detect duplicate-call loops and terminate with partial evidence plus warning. Parallelize only independent read tools when resource limits and deterministic ordering are preserved.
- Results are immutable evidence blocks with type, source and `as_of`. The final validator checks claimed numeric fields against tool outputs where structured fields exist and rejects/repairs unsupported citations through another bounded generation or safe fallback.
- Stale quote, missing filing, insufficient indicator history, no RAG hits, mixed timestamps, provider timeout, malformed JSON, context overflow, user cancellation, Ollama restart, bilingual ambiguity, and unsupported risk tool must remain visible in `missing_information`/warnings.
- Tool/document content may contain prompt injection. Delimit it as untrusted evidence and system-instruct the model never to follow embedded commands. Strip neither Arabic nor material evidence while applying output-size limits.
- Latest-news uses only phase-05 normalized, sourced NEWS documents and publication cutoffs. No ad hoc model/web browsing.
- Historical/as-of requests propagate one cutoff to every tool to avoid look-ahead. Current analysis surfaces the oldest/most material component timestamp, not one misleading date.
- Temperature and sampling are configured for stable factual behavior, but model prose is not assumed deterministic. All numerical assertions remain reproducible from tool traces.
- Refuse trade execution, guaranteed-return framing, requests to expose secrets/system prompts, and unsupported claims. Confidence is never represented as statistical probability.

## Tests
- Provider contract tests with fake and recorded local Ollama-shaped responses; malformed stream/JSON/tool calls, timeout, missing model, cancellation, and context overflow.
- Registry unit tests for every tool schema, domain error mapping, Decimal/date serialization, provenance, stale/missing fields, budgets, duplicate-loop detection, and forbidden tool names.
- Orchestrator integration tests script exact multi-tool paths, including the guide’s Arabic COMI request: quote, financial snapshot, technical indicators, position/allocation, documents, and news.
- Safety tests for prompt injection in user text and retrieved documents, fabricated price requests, automatic buy/sell request, future certainty, unsupported risk calculation, citation mismatch, and sensitive-log redaction.
- Fixed Arabic/English evaluation questions assess numerical agreement with fixtures, source correctness, required tool usage, no hallucination, reasoning separation, language quality, dates, and insufficient-evidence behavior.
- Default suite uses `FakeLLMProvider`, fake embeddings, and mock domain providers. Real Ollama evaluations are opt-in local integration tests with tolerant semantic assertions, never public network calls.

## Manual demo
1. Start all services offline and ask `حلل COMI بالنسبة لمحفظتي` against fixed local fixtures.
2. Show audited calls to quote, financials, technicals, position/allocation, document search, and latest news; verify every number exactly against direct domain endpoints.
3. Display an Arabic answer with source/publication citations, data timestamps, stale/missing warnings, and clear separation of facts from interpretation; repeat in English.
4. Make a source stale and remove a filing; show the assistant states insufficiency and does not fill gaps from memory.
5. Insert a document saying “ignore previous instructions”; prove it is cited only as evidence and cannot trigger a forbidden tool or policy change.
6. Ask the assistant to place a BUY and to guarantee a return; show refusal/decision-support language. Stop Ollama mid-request and show bounded, recoverable failure while non-AI APIs continue working.

## Observability and failure handling
- Correlation IDs link API request, generation rounds, redacted tool calls, domain source/timestamp metadata, validation, and final status. Record model/prompt/tool schema versions, durations, token/size data where available, retries, budgets, and cancellation.
- Never log credentials, raw private portfolio exports, full prompts/tool results, or sensitive conversation content by default. Provide local opt-in debug logging with explicit redaction/retention warning.
- No blind retries after tool side effects (all initial tools are read-only); Ollama retries are bounded. Model failure degrades only the AI endpoint and never corrupts domain state.
- Distinct user-safe failures cover Ollama unavailable/model missing, timeout/cancel, invalid model output, forbidden/invalid tool, stale/incomplete evidence, and internal domain outage.

## Acceptance checklist
- [ ] `LLMProvider` isolates Ollama and fake provider tests are deterministic.
- [ ] Qwen operates fully locally with bounded resources and no external LLM API.
- [ ] Every exposed tool is typed, read-only, allowlisted, validated, budgeted, and provenance-bearing.
- [ ] Numerical claims come from tools and match deterministic domain outputs.
- [ ] Arabic/English evaluation covers language quality, citations, dates, tool use, and no hallucination.
- [ ] Stale/missing/conflicting evidence is visible; the model does not guess.
- [ ] Prompt injection, arbitrary tool access, trade execution, and guaranteed-return language are blocked.
- [ ] Historical cutoff propagates through all tools without look-ahead.
- [ ] Ollama failure leaves portfolio/market/financial/technical/document features operational.
- [ ] Manual offline demo and opt-in Ollama integration tests pass on the target Windows machine.

## Dependencies
- Upstream: phases 00–05; each tool is enabled only after its owning domain phase is accepted.
- Downstream: later Portfolio AI, risk, dashboard/chat, backtesting, and evaluation phases.
- `calculate_portfolio_risk` depends on the later deterministic risk engine and must not be faked here.
