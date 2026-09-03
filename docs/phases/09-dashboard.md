# Phase 09 — Next.js Dashboard

> **Corresponds to:** Implementation Guide Phase 11 — Next.js Dashboard  
> **Goal:** Deliver a reliable, RTL/Arabic-ready Next.js dashboard that visualizes portfolio data, market data, financials, technicals, risk, and AI analysis. Build a thin, data-first portfolio UI first; only then expand to the full dashboard.  
> **RTL/Arabic requirement:** The application must support a full Arabic locale with right-to-left (RTL) layout, Arabic numerals/currency/date formatting, and right-to-left charts. English locale must remain LTR.

---

## 1. Prerequisites

| Prerequisite | Evidence required |
|--------------|-------------------|
| Backend API stable for portfolio, market, financials, technicals | `GET /api/portfolio`, `/api/stocks/{symbol}/quote`, `/api/stocks/{symbol}/financials`, `/api/stocks/{symbol}/technical` return valid JSON. |
| Phase 7 (Portfolio AI) complete | `POST /api/analysis/stock/{symbol}` and `POST /api/analysis/portfolio` return structured analysis. |
| Phase 8 (Risk Engine) complete | `GET /api/risk/portfolio` returns risk report and breach flags. |
| Design tokens / component library started | Tailwind config supports RTL and Arabic font; `dir` switching tested. |
| Authentication stub (optional) | User identity available to frontend for portfolio-scoped calls. |

---

## 2. Strategy: Thin Portfolio UI First, Full Dashboard Later

The implementation guide says: "Build the UI after the backend calculations are stable." Within the dashboard phase, the same rule applies: start with a thin, high-signal portfolio UI before adding charts, AI cards, and advanced pages.

### 2.1 Two-stage plan

| Stage | Scope | Pages | Purpose |
|-------|-------|-------|---------|
| **A. Thin Portfolio UI** | Portfolio management only; no AI, minimal charts | `/portfolio`, `/settings` | Prove end-to-end data flow and transaction management. |
| **B. Full Dashboard** | Add stocks, analysis, AI, risk, documents | `/dashboard`, `/stocks`, `/stocks/[symbol]`, `/analysis`, `/documents`, `/risk` | Full decision-support interface. |

**Decision:** Do not build Stage B pages until Stage A is stable and manually demonstrated. The backend exists before the UI; the thin UI exists before the full dashboard.

### 2.2 Why this order matters

- Portfolio calculations are the foundation. If the thin UI cannot add a transaction and show correct P&L, adding charts and AI will only hide the bug.
- The first milestone in the guide is: add stock, add BUY, add SELL, see holdings, average cost, market value, unrealized P&L, allocation, sector allocation. This is exactly Stage A.
- Stage B depends on every earlier phase (market, financials, technicals, RAG, AI, risk). Skipping ahead creates brittle UI code.

### 2.3 Stage A — Thin Portfolio UI (mandatory first)

Build the following minimal set of pages and components.

#### Pages

| Page | Route | Purpose |
|------|-------|---------|
| Portfolio list | `/portfolio` | View holdings, total value, total P&L, cash. |
| Add transaction | `/portfolio/transactions/new` | Add BUY, SELL, DIVIDEND, DEPOSIT, WITHDRAWAL, FEE. |
| Edit transaction | `/portfolio/transactions/[id]` | Edit/delete a transaction with recalculation. |
| Transaction history | `/portfolio/transactions` | Filterable list of all transactions. |
| Settings | `/settings` | Set risk limits and locale (ar/en). |

#### Components

| Component | Required data |
|-----------|---------------|
| `PortfolioSummary` | total_value, total_pnl, cash, number_of_holdings, largest_position |
| `HoldingTable` | symbol, quantity, average_cost, market_price, market_value, unrealized_pnl, allocation_percent |
| `TransactionForm` | symbol, type, quantity, price, fees, date, notes |
| `SectorAllocationSimple` | sector name, percent (horizontal bar or table) |
| `LocaleSwitcher` | toggle ar/en; sets `dir="rtl"`/`"ltr"` and `lang="ar"`/`"en"` |

#### API contracts for Stage A

```text
GET    /api/portfolio/summary
GET    /api/portfolio/holdings
GET    /api/portfolio/transactions
POST   /api/portfolio/transactions
PUT    /api/portfolio/transactions/{id}
DELETE /api/portfolio/transactions/{id}
GET    /api/stocks (autocomplete for transaction form)
GET    /api/settings
POST   /api/settings
```

**Exit gate A:** A user can add `COMI` at 90.00 EGP, add fees, sell half, and the summary/holdings/sector views show correct deterministic values. The transaction history is consistent.

### 2.4 Stage B — Full Dashboard (after Stage A)

Once Stage A is signed off, add the remaining pages and components.

#### Pages

| Page | Route | Purpose |
|------|-------|---------|
| Dashboard home | `/dashboard` | High-level overview, widgets, AI portfolio score. |
| Stock list | `/stocks` | Screener/list of tracked EGX stocks. |
| Stock detail | `/stocks/[symbol]` | Price, chart, financials, technicals, news, disclosures, AI analysis. |
| Analysis hub | `/analysis` | AI stock analysis and whole-portfolio analysis. |
| Risk dashboard | `/risk` | Risk report, breaches, rebalancing ideas. |
| Documents | `/documents` | Company reports, disclosures, RAG search. |
| Settings | `/settings` | Locale, risk limits, data sources. |

#### Components

| Component | Required data |
|-----------|---------------|
| `DashboardSummaryGrid` | portfolio value, today's P&L, total P&L, cash, holdings count, AI score |
| `PriceChart` | Lightweight Charts candlestick/line with EGP axis |
| `TechnicalPanel` | RSI, MACD, SMA 20/50/200 |
| `FinancialsPanel` | P/E, P/B, ROE, revenue growth, EPS growth |
| `NewsPanel` | latest news list with source and date |
| `DisclosuresPanel` | latest disclosures with source and date |
| `AIAnalysisCard` | recommendation, confidence, reasons, risks, data_as_of |
| `RiskPanel` | breaches, concentration, sector chart, volatility, drawdown |
| `DocumentSearch` | RAG query input and ranked results with citations |

#### API contracts for Stage B

```text
GET /api/dashboard/summary
GET /api/stocks
GET /api/stocks/{symbol}/quote
GET /api/stocks/{symbol}/history
GET /api/stocks/{symbol}/financials
GET /api/stocks/{symbol}/technical
GET /api/stocks/{symbol}/news
GET /api/stocks/{symbol}/disclosures
POST /api/analysis/stock/{symbol}
POST /api/analysis/portfolio
GET  /api/risk/portfolio
GET  /api/documents/search?query=...&symbol=...
```

**Exit gate B:** All dashboard pages load, charts render, AI analysis displays with citations, and risk panel shows breach badges.

---

## 3. Ordered Tasks

### 3.1 Set up Next.js project structure

```text
frontend/
├── app/
│   ├── (locale)/          # locale-aware route group
│   │   ├── ar/
│   │   └── en/
│   ├── portfolio/
│   ├── transactions/
│   ├── dashboard/
│   ├── stocks/
│   ├── analysis/
│   ├── risk/
│   ├── documents/
│   └── settings/
├── components/
│   ├── ui/                # buttons, inputs, badges, tables
│   ├── portfolio/
│   ├── dashboard/
│   ├── stocks/
│   ├── analysis/
│   └── risk/
├── lib/
│   ├── api.ts             # typed fetch wrappers
│   ├── i18n/
│   │   ├── ar.json
│   │   └── en.json
│   └── utils.ts
├── hooks/
├── types/
└── tests/
```

**Exit gate 3.1:** `npm run dev` starts without errors; TypeScript strict mode enabled.

### 3.2 Implement locale and RTL foundation

- Use `next-intl` or custom middleware to set locale from URL segment (`/ar/...` or `/en/...`).
- Apply `dir="rtl"` and `lang="ar"` to `<html>` when locale is Arabic.
- Load Arabic font (e.g., IBM Plex Sans Arabic or Noto Sans Arabic).
- Number formatting: use `Intl.NumberFormat` with `ar-EG` or `en-GB`.
- Date formatting:
  - Arabic UI: `DD/MM/YYYY`
  - English UI: `YYYY-MM-DD`
- Currency: always EGP; display as `ج.م 95.40` in Arabic and `EGP 95.40` in English.
- Percentages: suffix `%` in English, `٪` or `%` consistently in Arabic.

**Exit gate 3.2:** Locale switcher toggles layout direction, font, and formatting; no page reload errors.

### 3.3 Stage A: Build thin portfolio UI

Implement pages in this order:

1. `/portfolio` — summary + holdings table.
2. `/portfolio/transactions/new` — transaction form with validation.
3. `/portfolio/transactions` — transaction history.
4. `/portfolio/transactions/[id]` — edit/delete.
5. `/settings` — locale toggle and risk limits display.

**Exit gate 3.3:** Manual demo from Section 4.1 passes.

### 3.4 Stage A validation and tests

- Add Playwright tests for add/edit/delete transaction flows.
- Add unit tests for portfolio component calculations.
- Add RTL visual regression tests for `/portfolio`.

**Exit gate 3.4:** All Stage A tests pass; no regression in portfolio calculations.

### 3.5 Stage B: Build full dashboard pages

After Stage A sign-off, add:

1. `/dashboard` — summary grid and quick actions.
2. `/stocks` and `/stocks/[symbol]` — charts, financials, technicals, news.
3. `/analysis` — AI stock and portfolio analysis.
4. `/risk` — risk report and rebalancing ideas.
5. `/documents` — RAG search over disclosures and reports.

**Exit gate 3.5:** All dashboard pages render data from real or mock backend endpoints.

### 3.6 Implement charts for RTL

- Use TradingView Lightweight Charts or a charting library that supports RTL.
- Axis labels, tooltips, and legend must flip with locale.
- Candlestick series must use EGP price axis.

**Exit gate 3.6:** Stock detail page chart renders correctly in Arabic and English.

### 3.7 Implement AI analysis cards

- Display recommendation label with color.
- Show confidence as "72/100", never "72%".
- Show `data_as_of` and source citations.
- Arabic cards must have `dir="rtl"` and right-aligned citations.

**Exit gate 3.7:** AI analysis card matches `PortfolioAnalysisResponse` schema in both locales.

### 3.8 Implement risk dashboard

- Use risk report from Phase 8.
- Show breach badges, sector allocation chart, rebalancing ideas.
- RTL chart legend and progress bars.

**Exit gate 3.8:** Risk page matches `RiskReport` schema and shows Arabic warnings.

---

## 4. Tests and Manual Demos

### 4.1 Stage A manual demo script

1. Start backend and frontend locally.
2. Navigate to `/portfolio`.
3. Add a BUY transaction: `COMI`, 100 shares, 90.00 EGP, fees 10 EGP.
4. Verify:
   - Holdings table shows 100 shares, average cost 90.10 EGP.
   - Market value uses latest quote.
   - Unrealized P&L is correct.
   - Allocation shows 100% if only one holding.
5. Add a second BUY: `COMI`, 50 shares, 100.00 EGP, fees 5 EGP.
6. Verify average cost becomes `(100*90.10 + 50*100.10) / 150`.
7. Add a SELL: `COMI`, 30 shares, 110.00 EGP, fees 5 EGP.
8. Verify realized P&L and remaining quantity.
9. Delete the SELL transaction; verify holding reverts.
10. Switch to Arabic; confirm RTL layout and EGP formatting.

### 4.2 Stage B manual demo script

1. Open `/dashboard`; confirm widgets load.
2. Open `/stocks/COMI`; confirm:
   - Price and daily change displayed.
   - Chart loads with EGP axis.
   - RSI, MACD, SMA shown.
   - P/E, P/B, ROE, growth rates shown.
   - Latest news and disclosures listed.
   - AI analysis card rendered with recommendation and citations.
3. Open `/risk`; confirm breach badges and sector chart.
4. Open `/documents`; search "إيرادات COMI" and verify ranked results with citations.
5. Switch locale; confirm LTR/RTL flip and formatting.

### 4.3 Automated tests

| Test | Scope |
|------|-------|
| Transaction CRUD E2E | Playwright |
| Portfolio summary calculation | Component/unit |
| Locale switching | Playwright |
| RTL layout on `/portfolio` | Visual regression |
| RTL chart on `/stocks/[symbol]` | Visual regression |
| AI analysis card schema compliance | Component/unit |
| Risk panel breach rendering | Component/unit |
| Document search results | Component/unit |

---

## 5. Safety and Failure Behavior

| Scenario | Expected behavior |
|----------|-------------------|
| Backend unreachable | Show cached data with stale banner; disable add/edit until reconnected. |
| Backend returns 503 for AI | Hide AI card or show "AI analysis unavailable"; still show deterministic metrics. |
| Stale quote (>15 min) | Show amber stale badge on price; do not hide the value. |
| Empty portfolio | Show empty state with prompt to add a transaction; no division-by-zero errors. |
| Invalid transaction input | Form-level validation with Arabic/English error messages. |
| Locale file missing a key | Fallback to English key; log missing key. |
| Chart library fails to load | Degrade to a data table view. |
| AI analysis contains forbidden phrase | UI does not render the phrase; show generic analysis warning and log the incident. |
| User switches locale mid-session | Preserve current page and form state; re-fetch data with new locale headers if needed. |

---

## 6. Exit Gates

### Stage A exit gates

1. User can add/edit/delete transactions and see correct holdings/P&L.
2. Arabic and English locales render correctly with RTL/LTR switching.
3. Portfolio calculation tests pass.
4. E2E transaction flow tests pass.
5. Thin portfolio UI is signed off by reviewer.

### Stage B exit gates

1. All dashboard, stock, analysis, risk, and document pages load data.
2. Charts render correctly in both LTR and RTL.
3. AI analysis card displays structured response with citations and `data_as_of`.
4. Risk dashboard shows breaches and Arabic warnings.
5. RAG document search returns cited results in both languages.
6. Full dashboard is signed off by reviewer.

### Phase exit gate

The entire Phase 09 is complete only when both Stage A and Stage B exit gates are satisfied and the phase definition-of-done checklist is signed off.
