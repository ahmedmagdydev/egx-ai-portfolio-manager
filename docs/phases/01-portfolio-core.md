# Phase 01 — Portfolio Core

## Objective
Build the deterministic, auditable source of truth for one local user's EGX stocks, transactions, cash, holdings, cost basis, P&L, and allocations. This phase must work completely without an LLM or live market provider.

## Prerequisites
- Phase 00 accepted; PostgreSQL migrations, FastAPI validation, UTF-8, and test tooling work.
- Explicit conventions agreed for EGP monetary precision, quantity precision, UTC storage, user-entered trading date/time, cost-basis method, and sell-fee treatment.
- A fixed mock price set and transaction ledger are available for repeatable tests.

## Expected modules and artifacts
- `backend/app/models/` stock, transaction, holding projection, and cash-account persistence models.
- `backend/app/schemas/` validated create/read contracts.
- `backend/app/portfolio/` pure ledger and calculation functions.
- `backend/app/services/` transactional commands/queries; `backend/app/api/` portfolio routes.
- Migrations, deterministic fixtures, unit/integration/API tests, OpenAPI examples, and bilingual sample stock metadata.
- Holdings are rebuildable projections, not an independently editable truth.

## Schema/API changes
Tables expected from the guide, tightened with constraints:
- `stocks`: `id`, unique normalized `symbol`, `name_ar`, `name_en`, `sector`, `currency`, `exchange`, `created_at`, `updated_at`.
- `transactions`: `id`, nullable `symbol` where appropriate, enum `transaction_type` (`BUY`, `SELL`, `DIVIDEND`, `DEPOSIT`, `WITHDRAWAL`, `FEE`), `quantity`, `price`, `fees`, `transaction_date`, `notes`, `created_at`; retain immutable insertion order via ID for timestamp ties.
- `holdings`: unique `symbol`, `quantity`, `average_cost`, `updated_at` as a rebuildable projection.
- `cash_accounts`: unique `currency`, `balance`, `updated_at`.
Use fixed-precision decimal/numeric columns, checks for nonnegative fees and valid type-specific fields, foreign keys to stocks, and UTC audit timestamps.

Minimum API contract: stock list/create; transaction list/create/get (corrections by explicit reversal or documented delete/rebuild policy); portfolio summary; holdings; cash; allocation and sector allocation. Responses include currency and `calculated_at`; values serialize as decimal strings or one consistently documented lossless convention.

## Ordered tasks
1. Write accounting decisions and invariant examples before schema work: weighted-average cost, realized gain treatment, fees, dividends, cash effects, and oversell policy.
2. Add constrained migrations and Pydantic request/response schemas; normalize EGX symbols at the boundary while preserving Arabic/English names.
3. Implement pure Decimal-based ledger replay sorted by `transaction_date`, then immutable ID. Reject ambiguous or invalid rows before mutation.
4. Implement `calculate_average_cost`, market value, unrealized/realized P&L, portfolio value, position allocation, and sector allocation. Accept prices as explicit inputs from a mock in this phase.
5. Implement atomic transaction posting and projection rebuild. Lock relevant rows or serialize local writes so cash and holdings cannot diverge.
6. Expose APIs with stable errors and OpenAPI examples. Keep portfolio calculations outside route handlers and ORM callbacks.
7. Add deterministic fixtures covering complete lifecycle and expected values calculated independently by hand.
8. Add reconciliation/rebuild operation for development/repair and prove its result equals incremental posting.

## Algorithms and edge cases
- BUY: quantity increases; new cost basis equals `(old_qty*old_avg + buy_qty*price + allocated_buy_fees) / new_qty`. State whether fees are capitalized; use the same rule everywhere.
- SELL: validate quantity does not exceed available quantity; realized P&L equals proceeds net of sell fees minus sold quantity at pre-sale average cost. Remaining average cost is unchanged; when quantity reaches zero normalize average cost to zero.
- Cash: deposits increase, withdrawals decrease, buys reduce by gross consideration plus fees, sells increase by net proceeds, dividends increase, standalone fees decrease. Define whether negative cash is prohibited; default to reject unless explicitly configured later.
- Market value is `quantity * current_price`; unrealized P&L compares it with remaining cost basis. Total P&L separates realized, unrealized, dividends, and fees to avoid double counting.
- Allocation denominator includes holdings market value and cash; define behavior for zero/negative total (return empty/null ratios with warning, never divide by zero). Sector totals must reconcile to stock allocations.
- Reject zero/negative BUY/SELL quantity or price, negative fees, unknown symbols, currency mismatch, NaN/infinity, oversells, and duplicate idempotency keys where supported.
- Backdated transactions trigger deterministic replay of affected projections. Same-timestamp records use stable insertion order. Never use binary floating point or locale-sensitive parsing.
- Corporate actions, short selling, tax lots, FX conversion, and multi-user authorization are out of scope; return explicit unsupported errors rather than guessing.

## Tests
- Table-driven unit tests for every function with exact Decimal expectations, including partial/full sells, multiple buys, fees, dividends, deposits/withdrawals, zero portfolio, and rounding boundaries.
- Property/invariant tests: holdings equal buys minus sells; sum allocations is 100% within declared tolerance; projection rebuild equals incremental state; repeated reads are identical.
- Integration tests for constraints, rollback on failure, backdated replay, concurrent submissions, and Unicode Arabic/English stock records.
- API tests for success, validation errors, unknown symbols, oversell/insufficient cash, and deterministic ordering/serialization.
- No live prices: use `MockMarketDataProvider`-compatible fixtures or direct price maps. Freeze clock and IDs where snapshots are asserted.

## Manual demo
1. Create COMI with Arabic and English names and an EGP cash account; deposit EGP 100,000.
2. Post two BUYs with different prices/fees and show hand-reconciled quantity and weighted average cost.
3. Supply a fixed mock quote; show market value, unrealized P&L, portfolio/cash, stock allocation, and sector allocation.
4. Post a partial SELL and dividend; show realized P&L, unchanged remaining average cost, and cash reconciliation.
5. Attempt an oversell and prove the database remains unchanged. Rebuild projections and show identical results.

## Observability and failure handling
- Log command type, transaction ID, normalized symbol, correlation ID, duration, and result status; do not log private notes or full portfolio snapshots by default.
- Emit explicit reconciliation errors if ledger, holdings, or cash disagree. Database writes are atomic and rollback fully on any calculation/constraint failure.
- Error codes distinguish validation, unknown stock, duplicate request, insufficient holdings/cash, unsupported currency/action, and internal reconciliation failure.
- Summary responses expose `calculated_at`, valuation currency, and whether prices are mock/manual; never imply a mock quote is current.

## Acceptance checklist
- [ ] All tables, constraints, schemas, and APIs are documented and migrated reproducibly.
- [ ] Known ledgers produce exact deterministic results without an LLM.
- [ ] Every calculation has unit tests and key workflows have integration/API tests.
- [ ] Fees, dividends, cash, realized/unrealized P&L, and rounding conventions reconcile.
- [ ] Backdated replay and full projection rebuild are deterministic.
- [ ] Arabic/English metadata round-trips; symbols/currency are normalized safely.
- [ ] Invalid, duplicate, and oversell operations fail atomically with useful errors.
- [ ] Manual demo matches independent hand calculations.
- [ ] Corporate actions, FX, shorts, and multi-user behavior are explicitly deferred.

## Dependencies
- Upstream: phase 00.
- Downstream: phase 02 supplies trusted prices; phases 04 and 06 consume portfolio facts.
- Must not depend on phases 02–06, Ollama, or public network access.
