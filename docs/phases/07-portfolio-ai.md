# Phase 07 — Portfolio AI

> **Corresponds to:** Implementation Guide Phase 9 — Portfolio AI  
> **Goal:** Build a deterministic, tool-driven AI investment-analysis layer that returns a structured recommendation for a stock or an entire portfolio, never inventing market data, ratios, or prices.  
> **RTL/Arabic requirement:** All user-facing Arabic copy must support right-to-left (RTL) layout, numerals, date formatting (`DD/MM/YYYY`), and EGP currency formatting (`ج.م`).

---

## 1. Prerequisites

Before starting this phase, the following must be complete and passing their tests:

| Prerequisite | Evidence required |
|--------------|-------------------|
| Phase 6 (RAG) implemented | `GET /api/stocks/{symbol}/documents` returns ranked, cited chunks. |
| Phase 8 (Tool Calling) implemented | Tool schema registered and LLM can call at least `get_quote`, `get_financial_snapshot`, `get_technical_indicators`, `get_position`, `calculate_portfolio_allocation`, `search_documents`, `get_latest_news`. |
| Ollama `qwen3.5:9b` running locally | `ollama ps` shows model loaded; `/api/tags` reachable from the backend container. |
| Portfolio engine deterministic | Unit tests for average cost, P&L, allocation, sector allocation pass. |
| Market data fresh within 15 minutes | Quote endpoint returns `data_as_of` timestamp; stale-data guard is implemented. |
| Financial ratios deterministic | `calculate_pe`, `calculate_pb`, `calculate_roe`, etc. return reproducible values. |
| Technical indicators deterministic | RSI/MACD/SMA values reproducible for the same OHLCV window. |

> **Arabic UX prerequisite:** The response schema must expose `title_ar`, `reason_ar`, `risk_ar`, and `missing_information_ar` fields so the frontend can render Arabic without translating on the fly.

---

## 2. Ordered Tasks

### 2.1 Define the structured analysis response schema

Create a Pydantic schema `PortfolioAnalysisResponse` with the following fields. The LLM must populate every field; do not allow free-form text as the primary artifact.

```python
class PortfolioAnalysisResponse(BaseModel):
    symbol: str | None
    recommendation: RecommendationEnum      # BUY / ACCUMULATE / HOLD / REDUCE / SELL / WATCH
    confidence: int                       # 0-100; explicitly NOT a probability
    valuation_assessment: AssessmentEnum   # ATTRACTIVE / FAIR / RICH / INSUFFICIENT_DATA
    fundamental_assessment: AssessmentEnum # POSITIVE / NEUTRAL / NEGATIVE / INSUFFICIENT_DATA
    technical_assessment: AssessmentEnum   # BULLISH / NEUTRAL / BEARISH / INSUFFICIENT_DATA
    portfolio_assessment: AssessmentEnum  # FIT / OVERWEIGHT / HIGH_CONCENTRATION / UNDERWEIGHT / NO_POSITION
    reasons: list[str]
    reasons_ar: list[str]
    risks: list[str]
    risks_ar: list[str]
    missing_information: list[str]
    missing_information_ar: list[str]
    data_as_of: datetime
    sources: list[SourceCitation]
```

```python
class SourceCitation(BaseModel):
    source_type: str   # MARKET_DATA / FINANCIAL_STATEMENT / TECHNICAL_INDICATOR / DOCUMENT / NEWS / PORTFOLIO
    title: str
    title_ar: str | None
    published_at: datetime | None
    url: str | None
```

**Exit gate 2.1:** Schema validated with at least five sample JSON payloads and Arabic numerals/currency rendering tested in RTL mode.

### 2.2 Implement the analysis orchestrator service

Create `backend/app/services/portfolio_ai.py` with function:

```python
async def analyze_investment(symbol: str | None,
                               include_portfolio: bool = True,
                               user_id: str = "default") -> PortfolioAnalysisResponse
```

The orchestrator must:

1. Verify data freshness for market data; reject or warn if stale.
2. Call tools deterministically (do not call the LLM for calculations).
3. Build a context object containing only verified facts, metrics, and retrieved document chunks.
4. Send a structured system prompt + context to `LLMProvider`.
5. Parse the model output into `PortfolioAnalysisResponse`.
6. Attach `data_as_of` equal to the oldest market/financial timestamp used.

**Exit gate 2.2:** Integration test runs the full pipeline for a mocked `COMI` symbol and asserts every field is populated.

### 2.3 Write the system prompt for investment analysis

The prompt must instruct the model to:

- Use only the provided tools/facts; never invent prices or ratios.
- Distinguish between verified facts, calculated metrics, retrieved documents, interpretation, and assumptions.
- Not present `confidence` as a probability.
- Provide reasons and risks in both English and Arabic when the user query is Arabic.
- Cite sources for every factual claim.
- Refuse to issue buy/sell orders; label output as "decision-support analysis".
- Identify stale or missing data explicitly.
- Consider both the standalone stock case and its impact on the user's portfolio when `include_portfolio=True`.

**Exit gate 2.3:** Prompt is versioned in `docs/prompts/portfolio-analysis-v1.md` and reviewed for disallowed claims.

### 2.4 Implement single-stock analysis endpoint

```text
POST /api/analysis/stock/{symbol}
```

Request body:

```json
{
  "include_portfolio_context": true,
  "language": "ar"
}
```

Response: `PortfolioAnalysisResponse`.

**Exit gate 2.4:** Endpoint returns 200 with valid schema; returns 503 when Ollama is unavailable; returns 422 when symbol is unknown.

### 2.5 Implement whole-portfolio analysis endpoint

```text
POST /api/analysis/portfolio
```

Returns a top-level assessment plus a per-holding breakdown.

```python
class WholePortfolioAnalysis(BaseModel):
    overall_recommendation: RecommendationEnum
    overall_confidence: int
    concentration_risk: AssessmentEnum
    sector_exposure: AssessmentEnum
    cash_position: AssessmentEnum
    holdings: list[HoldingAnalysis]
    summary_ar: str
    summary_en: str
```

**Exit gate 2.5:** Endpoint produces a portfolio-level summary and ranks holdings by concentration and risk.

### 2.6 Add Arabic/RTL rendering contracts

Frontend contract:

- Arabic text fields must be rendered with `dir="rtl"` and `lang="ar"`.
- Numerals must be Eastern Arabic or standard Arabic numerals based on locale, but currency must remain clear (e.g., `ج.م 95.40`).
- Dates: `DD/MM/YYYY` for Arabic UI, `YYYY-MM-DD` for English UI.
- Recommendation labels must have Arabic equivalents:
  - BUY = شراء
  - ACCUMULATE = تراكم
  - HOLD = احتفاظ
  - REDUCE = تقليل
  - SELL = بيع
  - WATCH = مراقبة

**Exit gate 2.6:** Storybook/screenshot test for Arabic recommendation card exists.

### 2.7 Implement guardrails and logging

- Log every LLM request, tool call, and response to a non-sensitive audit table (`ai_analysis_logs`).
- Never log credentials, full document text, or portfolio balances at high verbosity.
- Store the raw LLM output for 30 days to enable debugging and hallucination audits.
- Add a post-processing validator that rejects responses containing forbidden phrases: "مضمون", "أرباح مضمونة", "سيرتفع بنسبة", "probability that the stock will".

**Exit gate 2.7:** Forbidden-phrase test passes and log schema reviewed.

---

## 3. Artifacts

| Artifact | Location | Purpose |
|----------|----------|---------|
| `PortfolioAnalysisResponse` schema | `backend/app/schemas/analysis.py` | Contract between AI layer and frontend. |
| Analysis orchestrator | `backend/app/services/portfolio_ai.py` | Coordinates tools, context, LLM, parsing. |
| System prompt | `docs/prompts/portfolio-analysis-v1.md` | Versioned, reviewed prompt. |
| Stock analysis endpoint | `backend/app/api/analysis.py` | REST contract. |
| Portfolio analysis endpoint | `backend/app/api/analysis.py` | REST contract. |
| AI analysis log table | PostgreSQL `ai_analysis_logs` | Audit and debugging. |
| Arabic label map | `frontend/lib/labels/ar.json` | RTL-safe recommendation labels. |
| Screenshot test | `frontend/tests/rtl/analysis-card.spec.ts` | Visual regression for Arabic card. |

---

## 4. Tests and Manual Demos

### Automated tests

1. **Schema validation test:** 10 valid/invalid payloads.
2. **Single-stock analysis test:** mock all tool returns, assert every field present and confidence `0-100`.
3. **Arabic field test:** assert `reasons_ar` and `risks_ar` are non-empty for Arabic queries.
4. **Stale-data warning test:** quote timestamp older than 15 minutes causes `missing_information` to include a stale-data warning.
5. **Forbidden-phrase test:** mock LLM output with disallowed phrase, assert post-processor rejects it.
6. **Source-citation test:** assert every reason has at least one source with `published_at`.

### Manual demo script

1. Log in to the local UI.
2. Add `COMI` holding with 100 shares at 90.00 EGP.
3. Navigate to `/stocks/COMI`.
4. Click "Analyze with AI".
5. Verify:
   - Recommendation appears in Arabic.
   - Confidence is shown as "72/100" not "72%".
   - "Data as of" matches the market data timestamp.
   - Each reason lists a source.
   - No guaranteed-return language.
6. Repeat in English and confirm LTR layout.

---

## 5. Safety and Failure Behavior

| Scenario | Expected behavior |
|----------|-------------------|
| Ollama unavailable | Return 503 with message: "AI analysis is temporarily unavailable. Calculated metrics are still shown below." |
| Model returns malformed JSON | Retry once with a stricter JSON prompt; if still failing, return 500 and log raw output for inspection. |
| Stale market data (>15 min) | Analysis proceeds with a `missing_information` warning; recommendation confidence capped at 60. |
| Missing financial statement | Set `fundamental_assessment` to `INSUFFICIENT_DATA`; add to `missing_information`. |
| Unknown symbol | Return 422; do not call LLM. |
| LLM invents a price | Post-processor rejects; fallback to deterministic metrics-only response. |
| User asks to place an order | Response must refuse and restate decision-support-only nature. |
| High concentration detected | Set `portfolio_assessment` to `HIGH_CONCENTRATION`; include explicit Arabic warning. |

---

## 6. Exit Gates

This phase is complete only when:

1. `POST /api/analysis/stock/{symbol}` returns valid, fully populated `PortfolioAnalysisResponse` for Arabic and English.
2. `POST /api/analysis/portfolio` returns a portfolio-level analysis with per-holding breakdown.
3. All automated tests pass and forbidden-phrase guard is active.
4. Arabic recommendation card renders correctly in RTL with proper numerals and dates.
5. Every recommendation includes `data_as_of` and source citations.
6. No automatic buy/sell action is possible through the analysis endpoint.
7. Stale/missing data is surfaced to the user, not hidden.
8. Phase definition-of-done checklist is signed off by the reviewer.
