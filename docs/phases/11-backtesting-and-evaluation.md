# Phase 11 — Backtesting and Evaluation

> **Corresponds to:** Implementation Guide Phases 15–16 — Backtesting, Evaluation + Optimization  
> **Goal:** Build a reproducible backtesting framework and an AI evaluation harness that validate the assistant's recommendations without look-ahead bias, then use the results to drive optimization.  
> **RTL/Arabic requirement:** Evaluation reports and backtest result dashboards must support Arabic/RTL rendering for metrics, dates, and currency.

---

## 1. Prerequisites

| Prerequisite | Evidence required |
|--------------|-------------------|
| Phase 7 (Portfolio AI) complete | Single-stock and whole-portfolio analysis endpoints return structured recommendations. |
| Phase 8 (Risk Engine) complete | Risk calculations and limits are deterministic. |
| Phase 9 Stage A complete | Portfolio UI can record transactions; transaction model stable. |
| Historical market data | At least 2 years of daily OHLCV for test symbols, stored locally or mocked for reproducibility. |
| Historical financial data | Quarterly financial statements for at least 3 periods for test symbols, or mocked. |
| Historical documents | Disclosures/news with `published_at` timestamps, or mocked corpus. |
| Deterministic LLM setup | Ollama `qwen3.5:9b` or a fixed seed path for reproducible inference. |

---

## 2. Ordered Tasks

### 2.1 Build the backtesting harness

Create `backend/app/services/backtest_engine.py`.

Core workflow:

```text
Historical date D
      ↓
Rebuild the world as it appeared on D
      ↓
Run AI analysis with only data available on or before D
      ↓
Capture recommendation and confidence
      ↓
Track forward performance from D+1 to D+holding_period
      ↓
Compute metrics and store result
```

#### Data scope on date D

- Market data: OHLCV up to D.
- Financial data: last published statement before D.
- Documents: only documents with `published_at <= D`.
- News: only news with `published_at <= D`.
- Portfolio: transactions with `transaction_date <= D`.

**Exit gate 2.1:** A synthetic backtest on a fixed fixture produces identical results across runs.

### 2.2 Implement look-ahead bias prevention

Rules:

- The backtest runner must filter every data query with an `as_of` parameter.
- No function may default to "latest" when running inside a backtest.
- The LLM must not be given any future text, prices, or dates.
- Mock market data provider must support `as_of` filtering.
- Logs must record the `as_of` date and data cutoffs for each run.

**Exit gate 2.2:** A unit test intentionally queries with `as_of=2025-06-01` and asserts no data after that date is returned.

### 2.3 Define backtest scenarios

Initial scenarios:

| Scenario | Description |
|----------|-------------|
| Single-stock BUY/HOLD | Generate recommendation for each symbol monthly; compare to buy-and-hold over 30/60/90 days. |
| Portfolio rebalancing | Run whole-portfolio analysis monthly; track a no-rebalance baseline. |
| Sector rotation stress | Concentrate portfolio in one sector; measure drawdown vs diversified baseline. |
| Stale-data stress | Run with 1-day, 7-day, and 30-day delayed market data; measure recommendation degradation. |
| Missing-financials stress | Run with missing financial statements; measure overconfidence. |

**Exit gate 2.3:** Each scenario has a JSON configuration and at least one recorded run.

### 2.4 Compute backtest metrics

For each recommendation track:

```python
class BacktestResult(BaseModel):
    run_id: str
    scenario: str
    symbol: str | None
    recommendation_date: date
    recommendation: RecommendationEnum
    confidence: int
    holding_period_days: int
    start_price: Decimal
    end_price: Decimal
    total_return_percent: Decimal
    max_drawdown_percent: Decimal
    benchmark_return_percent: Decimal | None
    excess_return_percent: Decimal | None
    win: bool                       # did the recommendation direction match return sign?
    transaction_cost_estimate: Decimal
    notes: str
```

Aggregate metrics per scenario:

- Annualized return
- Maximum drawdown
- Win rate (recommendation direction matched outcome)
- Sharpe ratio
- Benchmark excess return
- Turnover (rebalancing scenarios)
- Average confidence of correct vs incorrect recommendations

**Exit gate 2.4:** Metrics computed deterministically and exported to CSV and JSON.

### 2.5 Build the AI evaluation harness

Create `backend/tests/eval_ai/` with:

```text
fixtures/
  portfolio_a.json        # known portfolio state
  portfolio_b.json
  market_snapshot.json    # known prices on a fixed date
  financials_comi_q2.json
questions/
  en/
    q001_analyze_comi.json
    q002_concentration.json
    q003_cash.json
    q004_document_query.json
  ar/
    q001_analyze_comi.json
    ...
expected/
  q001.yaml
  ...
```

Each expected file contains:

- Expected tools to be called.
- Expected numerical bounds (e.g., P/E between 8.0 and 9.0).
- Required citations.
- Forbidden phrases.
- Required language.

**Exit gate 2.5:** `pytest tests/eval_ai` runs all questions and produces a pass/fail report.

### 2.6 Define evaluation criteria

| Criterion | How measured |
|-----------|--------------|
| Numerical accuracy | Extracted numbers within tolerance of fixture. |
| Tool usage | Correct tools called in correct order. |
| Source correctness | Citations match the fixture date and source type. |
| No hallucination | No invented prices, dates, ratios, or portfolio facts. |
| Reasoning quality | Rubric: 1-5 on clarity, dimension coverage, risk disclosure. |
| Arabic quality | Grammar check (manual), numerals/currency formatting, RTL-safe output. |
| Timestamps | `data_as_of` present and not in the future. |
| Safety | No trade execution or guaranteed-return language. |

**Exit gate 2.6:** Evaluation rubric documented and at least one reviewer signs off.

### 2.7 Run initial baseline evaluation

Run the evaluation harness on the current system and store the report:

```text
eval-reports/
  2026-09-02-baseline/
    results.json
    summary.md
    failures/
```

Record overall pass rate, per-question failures, and per-criterion scores.

**Exit gate 2.7:** Baseline report exists; any failure that blocks release is triaged.

### 2.8 Implement optimization loop

Use backtest and evaluation results to prioritize fixes:

1. Collect top failure categories (e.g., "Arabic date formatting", "missing source citations", "overconfident recommendation on stale data").
2. Create one ticket per category.
3. Update prompt, tool description, or post-processor.
4. Re-run evaluation; compare pass rate to baseline.
5. Accept only changes that improve or maintain pass rate.

**Exit gate 2.8:** At least one optimization cycle completed; results documented in `eval-reports/`.

### 2.9 Build evaluation/backtest UI (read-only)

Add a lightweight internal page at `/admin/evaluation` (optional, not user-facing):

- List backtest runs with CSV download.
- Show evaluation pass-rate chart.
- Display latest failure reasons.
- Support Arabic/RTL for internal reviewers.

**Exit gate 2.9:** Page loads and renders historical reports.

---

## 3. Artifacts

| Artifact | Location | Purpose |
|----------|----------|---------|
| Backtest engine | `backend/app/services/backtest_engine.py` | Reproducible backtesting core. |
| Backtest scenarios | `backend/tests/backtest/scenarios/` | JSON configs for each scenario. |
| Backtest fixtures | `backend/tests/backtest/fixtures/` | Synthetic market/financial/document data. |
| Backtest endpoint | `backend/app/api/backtest.py` | Trigger and retrieve backtest runs. |
| Backtest reports | `backend/tests/backtest/reports/` | Generated CSV/JSON results. |
| AI evaluation harness | `backend/tests/eval_ai/run_eval.py` | Runs fixed question dataset. |
| Evaluation fixtures | `backend/tests/eval_ai/fixtures/` | Known portfolio/market/financial states. |
| Evaluation questions | `backend/tests/eval_ai/questions/` | Arabic and English question sets. |
| Expected answers | `backend/tests/eval_ai/expected/` | Bounds, tools, citations, forbidden phrases. |
| Evaluation reports | `eval-reports/` | Baseline and iteration reports. |
| Admin UI | `frontend/app/[locale]/admin/evaluation/` | Internal report viewer. |

---

## 4. Tests and Manual Demos

### Automated tests

1. **Look-ahead test:** `as_of` filter prevents future data leakage.
2. **Determinism test:** same scenario produces identical metrics.
3. **Single-stock backtest test:** run on fixture COMI data; assert result schema.
4. **Portfolio backtest test:** run on fixture portfolio; assert no crashes with empty/missing data.
5. **Metric calculation test:** fixed return series yields expected return, drawdown, Sharpe.
6. **AI evaluation test:** `pytest tests/eval_ai` exits with report.
7. **Forbidden-phrase detection test:** evaluator flags guaranteed-return language.
8. **Arabic formatting test:** evaluator checks Arabic numerals and EGP formatting.

### Manual demo script

1. Open `/admin/evaluation`.
2. Trigger a backtest run for scenario "single-stock BUY/HOLD" over 90 days.
3. Wait for completion; verify CSV download has columns: `recommendation_date`, `symbol`, `recommendation`, `confidence`, `total_return_percent`, `win`.
4. Inspect a recommendation date and confirm `as_of` is before the forward window.
5. Run the AI evaluation harness from CLI:
   ```bash
   python -m pytest backend/tests/eval_ai -v
   ```
6. Review the generated report; identify top 3 failure categories.
7. Make a prompt tweak; re-run; confirm pass rate does not decrease.

---

## 5. Safety and Failure Behavior

| Scenario | Expected behavior |
|----------|-------------------|
| Future data leaks into backtest | Halt run and log error; result marked invalid. |
| Missing historical data for a date | Skip that symbol/date or flag as missing; do not interpolate. |
| LLM unavailable during backtest | Cache failed run; do not block other scenarios. |
| Recommendation enum unknown | Map to `WATCH`; log anomaly. |
| Evaluation question file malformed | `pytest` skips question and reports skip reason. |
| Backtest result differs from previous run | Diff report generated; investigator reviews data/model/prompt changes. |
| Evaluation pass rate drops | Block release; require prompt/model/data fix. |
| Benchmark data unavailable | Report `benchmark_return_percent=None`; do not invent benchmark. |
| Transaction cost assumption missing | Use default 0.5% round-trip; document assumption in report. |

---

## 6. Exit Gates

This phase is complete only when:

1. Backtest engine runs without look-ahead bias on historical data.
2. At least three backtest scenarios are defined and produce stored reports.
3. AI evaluation harness runs a fixed question set with documented criteria.
4. Baseline evaluation report is saved with overall pass rate and per-criterion scores.
5. At least one optimization cycle is completed and pass rate is stable or improved.
6. Evaluation UI (or CLI report) is accessible to internal reviewers.
7. No recommendation is released for personal decision support if it fails the safety or hallucination criteria.
8. Phase definition-of-done checklist is signed off by the reviewer.
