# Phase 10 — AI Chat

> **Corresponds to:** Implementation Guide Phase 12 — AI Chat  
> **Goal:** Deliver a dedicated conversational assistant that answers natural-language investment questions in Arabic or English by calling deterministic tools, never inventing data, and always citing sources and timestamps.  
> **RTL/Arabic requirement:** The chat interface must be fully RTL when the user writes in Arabic or selects Arabic locale; messages, citations, and input controls must flow right-to-left.

---

## 1. Prerequisites

| Prerequisite | Evidence required |
|--------------|-------------------|
| Phase 7 (Portfolio AI) complete | Structured analysis endpoint returns recommendation with sources and `data_as_of`. |
| Phase 8 (Risk Engine) complete | Risk report endpoint returns breaches and limits. |
| Phase 9 Stage A complete | Thin portfolio UI can add transactions and display holdings. |
| Tool calling pipeline stable | LLM can call `get_quote`, `get_position`, `get_financial_snapshot`, `get_technical_indicators`, `calculate_portfolio_allocation`, `calculate_sector_allocation`, `calculate_portfolio_risk`, `search_documents`, `get_latest_news`. |
| Ollama `qwen3.5:9b` running locally | Model responds within acceptable latency for chat (target <10s first token, streaming recommended). |
| Chat persistence schema | `chat_sessions` and `chat_messages` tables exist. |

---

## 2. Ordered Tasks

### 2.1 Define chat data model

Create PostgreSQL tables:

```text
chat_sessions
-------------
id
title
title_ar
user_id
created_at
updated_at

chat_messages
---------------
id
session_id
role           # user | assistant | tool | system
content
tool_calls     # JSON array of tool calls made by assistant
tool_results   # JSON array of tool results
language       # ar | en | mixed
created_at
```

**Exit gate 2.1:** Migrations create tables; messages can be inserted and retrieved by session.

### 2.2 Design the chat API contract

Endpoints:

```text
GET  /api/chat/sessions
POST /api/chat/sessions
GET  /api/chat/sessions/{session_id}/messages
POST /api/chat/sessions/{session_id}/messages   # send a user message
DELETE /api/chat/sessions/{session_id}
```

Request body for sending a message:

```json
{
  "content": "حلل محفظتي بالكامل",
  "language": "ar"
}
```

Response stream (SSE):

```text
event: tool_call
data: {"tool":"get_portfolio","arguments":{}}

event: tool_result
data: {"tool":"get_portfolio","result":{...}}

event: delta
data: {"content":"بناءً على بيانات محفظتك..."}

event: done
data: {"message_id":"...","sources":[...],"data_as_of":"..."}
```

**Exit gate 2.2:** SSE endpoint streams tool calls, results, and final answer without buffering the entire response.

### 2.3 Implement the chat orchestrator service

Create `backend/app/services/chat_service.py`:

```python
async def stream_chat_response(session_id: str,
                                user_message: str,
                                language: str,
                                user_id: str = "default") -> AsyncGenerator[ChatEvent, None]:
    # 1. Load session history (last N messages for context).
    # 2. Detect intent and required tools.
    # 3. Stream tool calls to client.
    # 4. Execute tools deterministically.
    # 5. Stream tool results (sanitized, no credentials).
    # 6. Build final context and call LLM.
    # 7. Stream answer tokens.
    # 8. Persist final message with citations and data_as_of.
```

The orchestrator must:

- Limit context window to avoid exceeding model context length (keep last 10 messages or token budget).
- Execute tools in parallel where independent.
- Retry transient Ollama errors once.
- Sanitize tool results before streaming (remove credentials, internal IDs).
- Tag the final message with the oldest market/financial timestamp used.

**Exit gate 2.3:** Unit test mocks LLM and tools; asserts correct sequence of `tool_call`, `tool_result`, and `delta` events.

### 2.4 Write the chat system prompt

The system prompt must include:

- Identity: "You are an Egyptian Stock Exchange investment research assistant."
- Tool-use mandate: "For current or numerical information, use the available tools."
- No-invention rule: "Do not invent prices, ratios, news, disclosures, or portfolio data."
- Decision-support only: "Do not execute trades. Recommendations are analysis, not guaranteed outcomes."
- Source citation: "Cite the source and publication date for every factual claim."
- Date/time tagging: "Always state the date/time of market data used."
- Arabic/English rule: "Respond in the user's language. If mixed, default to Arabic for Arabic-script queries."
- Refusal handling: "If information is insufficient, say so explicitly."

**Exit gate 2.4:** Prompt versioned in `docs/prompts/chat-assistant-v1.md`; reviewed for disallowed claims.

### 2.5 Build the chat UI

Page route: `/chat` or `/analysis/chat`.

Components:

- `ChatSidebar` — list of sessions with new-session button.
- `ChatMessageList` — scrollable message container.
- `ChatMessage` — user (RTL/LTR aligned) and assistant bubbles.
- `ToolCallIndicator` — spinning or completed tool icon with tool name.
- `CitationPanel` — expandable sources attached to assistant message.
- `ChatInput` — textarea with send button and language auto-detect.

RTL requirements:

- Arabic user messages align right, English align left.
- Assistant Arabic text is right-aligned with `dir="rtl"`.
- Citation list flows right-to-left in Arabic.
- Send button positioned on the left in RTL mode.
- Placeholder text localized.

**Exit gate 2.5:** UI loads in Arabic and English; messages persist after refresh.

### 2.6 Add intent routing and guardrails

Classify incoming messages to decide which tools to expose:

| Intent | Required tools |
|--------|---------------|
| portfolio_overview | get_portfolio, calculate_portfolio_allocation, calculate_sector_allocation, calculate_portfolio_risk |
| stock_analysis | get_quote, get_financial_snapshot, get_technical_indicators, search_documents, get_latest_news, get_position |
| sector_concentration | get_portfolio, calculate_sector_allocation, calculate_portfolio_risk |
| document_question | search_documents, get_financial_snapshot |
| what_if_cash | get_portfolio, get_quote, calculate_portfolio_allocation |
| risk_question | calculate_portfolio_risk, get_risk_limits |

Guardrails:

- Block prompts that request trade execution: respond with refusal and decision-support disclaimer.
- Block requests for "guaranteed" returns: respond with risk disclaimer.
- If tool output is missing, do not fabricate; add to `missing_information`.

**Exit gate 2.6:** Intent routing test covers each intent and asserts correct tools are invoked.

### 2.7 Implement citation and provenance display

Every assistant message that uses tools must include a `sources` array:

```json
{
  "sources": [
    {
      "type": "MARKET_DATA",
      "title": "COMI quote",
      "title_ar": "سعر COMI",
      "published_at": "2026-09-02T14:30:00Z"
    },
    {
      "type": "DOCUMENT",
      "title": "COMI Q2 2026 Earnings Release",
      "title_ar": "نتائج COMI الربع الثاني 2026",
      "published_at": "2026-08-15T00:00:00Z"
    }
  ]
}
```

UI displays sources as chips that expand to show full title and date.

**Exit gate 2.7:** Sources rendered in Arabic and English; missing `published_at` shown as "date unknown".

### 2.8 Add chat evaluation harness

Create a static evaluation dataset in `backend/tests/eval_chat/`:

```text
q1: "حلل COMI"
q2: "هل عندي تركيز زائد في قطاع معين؟"
q3: "ما أكبر 3 مخاطر في محفظتي؟"
q4: "ما الذي تغير في EAST منذ آخر تقرير؟"
q5: "لو عندي 100,000 جنيه إضافية، ما الخيارات الموجودة في محفظتي؟"
```

Evaluation criteria:

- Numerical accuracy vs known test fixtures.
- Correct tool usage.
- Source citation presence.
- No hallucination (no invented prices, dates, figures).
- Arabic quality (grammar, numerals, EGP formatting).
- Response contains `data_as_of`.

**Exit gate 2.8:** At least 80% of evaluation questions pass on a fixed test fixture before release.

---

## 3. Artifacts

| Artifact | Location | Purpose |
|----------|----------|---------|
| Chat DB migrations | `backend/alembic/versions/..._chat.py` | Persist sessions and messages. |
| Chat schemas | `backend/app/schemas/chat.py` | API contracts. |
| Chat orchestrator | `backend/app/services/chat_service.py` | Streaming response logic. |
| Chat endpoints | `backend/app/api/chat.py` | REST/SSE API. |
| System prompt | `docs/prompts/chat-assistant-v1.md` | Versioned prompt. |
| Chat page | `frontend/app/[locale]/chat/page.tsx` | Main UI. |
| Chat components | `frontend/components/chat/` | Reusable chat UI pieces. |
| Evaluation dataset | `backend/tests/eval_chat/` | Regression tests for AI answers. |
| Arabic chat labels | `frontend/lib/labels/ar-chat.json` | RTL-safe chat strings. |

---

## 4. Tests and Manual Demos

### Automated tests

1. **Message persistence test:** create session, send message, reload, assert history.
2. **Streaming event order test:** tool_call → tool_result → delta → done.
3. **Arabic response test:** Arabic query produces Arabic final answer.
4. **Tool-usage test:** mock LLM forces a tool call; orchestrator executes it.
5. **Citation test:** every answer based on tools contains at least one source.
6. **Refusal test:** "buy 100 shares of COMI now" triggers trade-execution refusal.
7. **Stale data test:** stale quote causes `data_as_of` warning in answer.
8. **Evaluation harness:** run fixed dataset and report pass rate.

### Manual demo script

1. Open `/chat`.
2. Type: "حلل محفظتي بالكامل".
3. Observe:
   - Tool call indicators appear for `get_portfolio`, `calculate_portfolio_allocation`, `calculate_portfolio_risk`.
   - Assistant responds in Arabic.
   - Response mentions data timestamp.
   - Sources are listed and clickable.
4. Type: "Should I buy more COMI?"
5. Observe:
   - Response is in English.
   - Tools `get_quote`, `get_financial_snapshot`, `get_technical_indicators`, `get_position` are called.
   - Recommendation is decision-support only.
6. Type: "Execute a buy order for COMI."
7. Observe refusal: "I cannot execute trades. This application is decision-support only."
8. Refresh page; confirm session history remains.

---

## 5. Safety and Failure Behavior

| Scenario | Expected behavior |
|----------|-------------------|
| Ollama unreachable | Stream `event: error` with message: "AI assistant is unavailable. Calculated data is still available in the dashboard." |
| Model returns non-Arabic for Arabic query | Post-process or prompt instructs Arabic; if persistent, log and warn user. |
| Model invents a price | Post-processor checks against latest tool result; mismatches trigger warning and removal of invented claim. |
| Tool fails | Stream tool error; assistant must say the data is unavailable, not fabricate. |
| Session not found | Return 404; UI redirects to new session. |
| Message exceeds context length | Summarize older turns; keep last N tokens within model budget. |
| User sends PII | Do not store raw PII in logs; sanitize before persistence. |
| LLM attempts to call non-existent tool | Reject tool call; respond that the action is unsupported. |
| Citation missing publication date | Display "date unknown / التاريخ غير متوفر". |
| High latency (>15s first token) | Show typing indicator and timeout message after 30s. |

---

## 6. Exit Gates

This phase is complete only when:

1. `/api/chat/sessions/{id}/messages` streams tool calls, results, and answers reliably.
2. Arabic and English queries produce correctly localized responses with proper RTL layout.
3. Every factual answer cites sources and timestamps.
4. Trade-execution requests are refused with a clear disclaimer.
5. Chat history persists and reloads correctly.
6. Evaluation harness reports ≥80% pass rate on fixed test fixtures.
7. No automatic trade execution is possible through chat.
8. Phase definition-of-done checklist is signed off by the reviewer.
