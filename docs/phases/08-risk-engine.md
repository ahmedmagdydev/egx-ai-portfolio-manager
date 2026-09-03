# Phase 08 — Portfolio Risk Engine

> **Corresponds to:** Implementation Guide Phase 10 — Portfolio Risk Engine  
> **Goal:** Add deterministic portfolio risk calculations, configurable exposure limits, and Arabic/RTL reporting so the AI and dashboard can explain risk in context without inventing limits or metrics.  
> **RTL/Arabic requirement:** Risk cards, sector allocation charts, and limit breach warnings must render right-to-left in Arabic mode; numerals and percentages must follow Arabic UX conventions.

---

## 1. Prerequisites

| Prerequisite | Evidence required |
|--------------|-------------------|
| Phase 1 portfolio engine complete | Holdings, transactions, cash, P&L calculations are stable and unit-tested. |
| Phase 2 market data complete | Historical prices available per symbol for at least 90 trading days. |
| Phase 3 financial data complete | Sector tags exist on every stock record. |
| Phase 6 RAG implemented | Optional: risk engine can cite disclosures in risk reports. |
| Configurable limits decided | `portfolio_limits` table or config exists with `max_single_position`, `max_sector_exposure`, `min_cash`. |

---

## 2. Ordered Tasks

### 2.1 Define risk configuration schema

Create `RiskLimits` configuration. Values must be version-controlled or stored in a configuration table, never hard-coded.

```python
class RiskLimits(BaseModel):
    max_single_position_percent: Decimal   # e.g., 25.0
    max_sector_exposure_percent: Decimal   # e.g., 40.0
    min_cash_percent: Decimal              # e.g., 10.0
    max_portfolio_volatility_annual: Decimal | None  # optional
    max_drawdown_percent: Decimal | None   # optional
    rebalancing_threshold_percent: Decimal = 5.0
```

Expose admin/settings endpoints:

```text
GET  /api/settings/risk-limits
POST /api/settings/risk-limits
```

**Exit gate 2.1:** Changing a limit immediately changes risk flags in the next calculation; no code redeploy required.

### 2.2 Build deterministic risk calculation service

Create `backend/app/services/risk_engine.py` with the following functions. All functions must be pure and unit-tested.

```python
def calculate_position_concentration(holdings: list[Holding], total_value: Decimal) -> dict[str, Decimal]
def calculate_sector_allocation(holdings: list[Holding], stocks: dict[str, Stock]) -> dict[str, Decimal]
def calculate_cash_percentage(cash: Decimal, total_value: Decimal) -> Decimal
def calculate_portfolio_volatility(holdings: list[Holding], prices_df: pd.DataFrame, window_days: int = 90) -> Decimal | None
def calculate_max_drawdown(holdings: list[Holding], prices_df: pd.DataFrame, window_days: int = 252) -> Decimal | None
def calculate_correlation_matrix(holdings: list[Holding], prices_df: pd.DataFrame) -> pd.DataFrame | None
def calculate_beta(holdings: list[Holding], prices_df: pd.DataFrame, benchmark_df: pd.DataFrame) -> Decimal | None
def calculate_sharpe_ratio(holdings: list[Holding], prices_df: pd.DataFrame, risk_free_rate_annual: Decimal) -> Decimal | None
```

Implementation notes:

- Portfolio volatility: compute daily returns for total portfolio value series, then annualized standard deviation.
- Maximum drawdown: use portfolio-level cumulative value; report positive percentage (e.g., `12.5` for 12.5%).
- Correlation: only include pairs with ≥30 overlapping observations; mark others as `None`.
- Beta: only compute if a reliable EGX benchmark series is available; otherwise report `None` and add to missing data.
- Sharpe: use EGP risk-free rate (e.g., 91-day T-bill) if available; otherwise configurable default.

**Exit gate 2.2:** Unit tests for each function with fixed inputs produce deterministic outputs to 4 decimal places.

### 2.3 Implement risk flags and breach detection

Create `RiskReport` schema:

```python
class RiskBreach(BaseModel):
    rule: str                            # e.g., MAX_SINGLE_POSITION
    severity: str                      # WARNING | CRITICAL
    current_value: Decimal
    limit_value: Decimal
    message_en: str
    message_ar: str
    suggested_action_en: str
    suggested_action_ar: str

class RiskReport(BaseModel):
    total_portfolio_value: Decimal
    cash_percent: Decimal
    largest_position_symbol: str
    largest_position_percent: Decimal
    sector_exposure: dict[str, Decimal]
    largest_sector: str
    largest_sector_percent: Decimal
    annualized_volatility: Decimal | None
    max_drawdown: Decimal | None
    beta: Decimal | None
    sharpe_ratio: Decimal | None
    correlation_matrix: dict[str, dict[str, Decimal]] | None
    breaches: list[RiskBreach]
    missing_data: list[str]
    missing_data_ar: list[str]
    data_as_of: datetime
```

**Exit gate 2.3:** Breach detection test asserts `MAX_SINGLE_POSITION` and `MAX_SECTOR_EXPOSURE` flags when synthetic portfolio exceeds limits.

### 2.4 Expose risk endpoints

```text
GET /api/risk/portfolio
GET /api/risk/portfolio/summary
GET /api/risk/stock/{symbol}
```

`GET /api/risk/stock/{symbol}` returns the standalone risk of a single position plus its contribution to total portfolio volatility and concentration.

**Exit gate 2.4:** All endpoints return valid `RiskReport` or `404` for unknown symbols.

### 2.5 Integrate risk into AI analysis

Update the Phase 7 analysis orchestrator to call `calculate_portfolio_risk()` when `include_portfolio=True`.

The AI must be able to explain:

- Position concentration relative to `max_single_position_percent`.
- Sector concentration relative to `max_sector_exposure_percent`.
- Cash position relative to `min_cash_percent`.
- Volatility, drawdown, beta, and Sharpe where data is available.

Add to tool list:

```text
calculate_portfolio_risk()
get_risk_limits()
```

**Exit gate 2.5:** AI analysis for a concentrated portfolio produces `portfolio_assessment=HIGH_CONCENTRATION` and Arabic warning citing the breach.

### 2.6 Arabic/RTL risk UX contract

- Risk cards must support `dir="rtl"` and Arabic labels.
- Sector allocation chart: legend and tooltips must flip for RTL; percentages displayed as `٪` or `%` consistently.
- Limit breach badges use semantic colors:
  - CRITICAL: red (`خطر`)
  - WARNING: amber (`تنبيه`)
- Progress bars for concentration must fill from right in RTL mode.
- Cash gauge: green when above `min_cash_percent`, amber near boundary, red below.

Arabic risk label map:

| English | Arabic |
|---------|--------|
| Position concentration | تركيز المركز |
| Sector exposure | تعرض القطاع |
| Cash percentage | نسبة النقد |
| Portfolio volatility | تقلب المحفظة |
| Maximum drawdown | أقصى انخفاض |
| Beta | بيتا |
| Sharpe ratio | نسبة شارب |
| Correlation | الارتباط |

**Exit gate 2.6:** RTL screenshot tests for risk summary card and sector chart pass.

### 2.7 Add rebalancing suggestions (informational only)

Generate a read-only "rebalancing idea" list based on deviation from target allocation. The AI may cite these ideas but must not execute trades.

```python
class RebalancingSuggestion(BaseModel):
    symbol: str
    action: str                 # REDUCE / INCREASE / HOLD
    action_ar: str
    current_percent: Decimal
    target_percent: Decimal
    delta_shares_estimate: int | None
    reason_ar: str
    reason_en: str
```

**Exit gate 2.7:** Suggestions respect `rebalancing_threshold_percent`; no order execution endpoint is created.

---

## 3. Artifacts

| Artifact | Location | Purpose |
|----------|----------|---------|
| `RiskLimits` schema | `backend/app/schemas/risk.py` | Configurable exposure limits. |
| Risk engine service | `backend/app/services/risk_engine.py` | Deterministic risk calculations. |
| `RiskReport` schema | `backend/app/schemas/risk.py` | API/AI contract. |
| Risk endpoints | `backend/app/api/risk.py` | REST contract. |
| Risk limits settings | `backend/app/api/settings.py` | Admin configuration. |
| Risk-to-AI bridge | `backend/app/services/portfolio_ai.py` | Feeds risk report into analysis. |
| Arabic risk labels | `frontend/lib/labels/ar-risk.json` | RTL-safe risk terminology. |
| RTL risk tests | `frontend/tests/rtl/risk-summary.spec.ts` | Visual regression. |

---

## 4. Tests and Manual Demos

### Automated tests

1. **Position concentration test:** 30% position against 25% limit → CRITICAL breach.
2. **Sector concentration test:** 45% financials against 40% limit → WARNING or CRITICAL based on tolerance.
3. **Cash test:** 8% cash against 10% minimum → WARNING.
4. **Volatility/drawdown test:** fixed price series yields deterministic values.
5. **Correlation matrix test:** insufficient overlap returns `None`, not a spurious value.
6. **Beta test:** missing benchmark returns `None` with explanatory `missing_data` entry.
7. **AI integration test:** high-concentration portfolio triggers Arabic warning.

### Manual demo script

1. Set limits: max single position 25%, max sector 40%, min cash 10%.
2. Create a portfolio: 35% in `COMI`, 45% in financials, 5% cash.
3. Open `/portfolio/risk`.
4. Confirm:
   - Red CRITICAL badge for `COMI` concentration.
   - Amber WARNING badge for sector exposure.
   - Red badge for low cash.
   - Arabic labels render RTL.
   - Sector chart legend is right-aligned.
5. Run AI analysis on the portfolio and confirm it warns about the financial-sector concentration.

---

## 5. Safety and Failure Behavior

| Scenario | Expected behavior |
|----------|-------------------|
| Missing 90-day price history | Volatility and drawdown return `None`; added to `missing_data`. |
| Missing benchmark | Beta returns `None`; no fallback to a guessed benchmark. |
| Negative total portfolio value | Return 422; risk calculations require non-negative total value. |
| All cash, no holdings | Volatility/drawdown/beta/sharpe are `None`; cash percent is 100. |
| Invalid risk limits (e.g., >100%) | Validation error on POST; existing limits remain unchanged. |
| AI attempts to set limits via tool | Tool is read-only; no tool can modify limits. |
| Correlation with insufficient data | Marked as unavailable, not approximated. |
| Rebalancing threshold = 0 | Suggestions disabled to avoid noise. |

---

## 6. Exit Gates

This phase is complete only when:

1. Every deterministic risk function has passing unit tests.
2. `GET /api/risk/portfolio` returns a complete `RiskReport` with breach flags.
3. Risk limits are configurable without redeploying the application.
4. AI analysis incorporates risk report and can explain breaches in Arabic and English.
5. Arabic risk UI renders correctly in RTL, including charts and badges.
6. No endpoint can execute a trade or rebalance automatically.
7. Phase definition-of-done checklist is signed off by the reviewer.
