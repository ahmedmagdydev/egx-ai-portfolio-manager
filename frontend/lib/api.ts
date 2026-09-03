export type HealthResponse = {
  status: string;
  service: string;
  version: string;
  checks: Record<string, unknown>;
  timestamp: string;
  detail?: Record<string, string>;
};

export type TransactionType =
  | "BUY"
  | "SELL"
  | "DEPOSIT"
  | "WITHDRAWAL"
  | "DIVIDEND";

export type Stock = {
  id: string;
  symbol: string;
  name_en: string;
  name_ar: string | null;
  sector: string | null;
  currency: string;
  is_active: boolean;
  created_at: string;
  generated_at: string;
};

export type TransactionInput = {
  type: TransactionType;
  symbol?: string;
  quantity?: string;
  price?: string;
  fees?: string;
  amount?: string;
  executed_at: string;
  note?: string;
};

export type Transaction = TransactionInput & {
  id: string;
  stock_id: string | null;
  quantity: string | null;
  price: string | null;
  fees: string;
  amount: string | null;
  symbol: string | null;
  sequence: number;
  note: string | null;
  created_at: string;
  currency: string;
  generated_at: string;
};

export type TransactionPage = {
  items: Transaction[];
  total: number;
  limit: number;
  offset: number;
  currency: string;
  generated_at: string;
};

export type Price = {
  value: string | null;
  source: string | null;
  observed_at: string | null;
  freshness: "fresh" | "stale" | null;
  status: "fresh" | "stale" | "unavailable";
};

export type Holding = {
  symbol: string;
  quantity: string;
  avg_cost: string;
  total_cost: string;
  market_value: string | null;
  unrealized_pnl: string | null;
  unrealized_pnl_pct: string | null;
  realized_pnl: string;
  price: Price;
};

export type PortfolioSummary = {
  total_market_value: string;
  total_cost: string;
  cash: string;
  total_value: string;
  realized_pnl: string;
  unrealized_pnl: string;
  data_as_of: string | null;
  unpriced_count: number;
};

export type HoldingsResponse = {
  holdings: Holding[];
  summary: PortfolioSummary;
  data_as_of: string | null;
  currency: string;
  generated_at: string;
};

export type AllocationLine = {
  name: string;
  value: string;
  weight: string;
};

export type AllocationResponse = {
  by_symbol: AllocationLine[];
  by_sector: AllocationLine[];
  cash: AllocationLine;
  unpriced_symbols: string[];
  currency: string;
  generated_at: string;
};

export type ApiErrorBody = {
  code?: string;
  message?: string;
  details?: Record<string, unknown> | null;
};

export class ApiError extends Error {
  code: string;
  details: Record<string, unknown> | null;
  status: number;

  constructor(
    code: string,
    message: string,
    details: Record<string, unknown> | null = null,
    status = 0,
  ) {
    super(message);
    this.name = "ApiError";
    this.code = code;
    this.details = details;
    this.status = status;
  }
}

export function isApiUnavailable(error: unknown): boolean {
  return (
    !(error instanceof ApiError) ||
    error.status >= 500 ||
    error.code === "HTTP_ERROR"
  );
}

export function getApiBaseUrl(): string {
  return process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000";
}

async function requestJson<T>(
  path: string,
  options: RequestInit = {},
  fetchImpl: typeof fetch = fetch,
): Promise<T> {
  const response = await fetchImpl(`${getApiBaseUrl()}${path}`, {
    ...options,
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
  });
  const body = (await response.json().catch(() => ({}))) as ApiErrorBody;
  if (!response.ok) {
    throw new ApiError(
      body.code || "HTTP_ERROR",
      body.message || `API request failed: ${response.status}`,
      body.details || null,
      response.status,
    );
  }
  return body as T;
}

export async function fetchHealth(
  path: string,
  fetchImpl: typeof fetch = fetch,
): Promise<HealthResponse> {
  const response = await fetchImpl(`${getApiBaseUrl()}${path}`, {
    cache: "no-store",
  });
  if (!response.ok) {
    throw new Error(`API request failed: ${response.status}`);
  }
  return response.json() as Promise<HealthResponse>;
}

export function fetchLiveness(
  fetchImpl: typeof fetch = fetch,
): Promise<HealthResponse> {
  return fetchHealth("/health/live", fetchImpl);
}

export function listStocks(fetchImpl: typeof fetch = fetch): Promise<Stock[]> {
  return requestJson<Stock[]>("/portfolio/stocks", {}, fetchImpl);
}

export function createStock(
  body: Pick<Stock, "symbol" | "name_en" | "name_ar" | "sector">,
  fetchImpl: typeof fetch = fetch,
): Promise<Stock> {
  return requestJson<Stock>(
    "/portfolio/stocks",
    {
      method: "POST",
      body: JSON.stringify(body),
    },
    fetchImpl,
  );
}

export function listTransactions(
  params: { symbol?: string; limit?: number; offset?: number } = {},
  fetchImpl: typeof fetch = fetch,
): Promise<TransactionPage> {
  const search = new URLSearchParams();
  if (params.symbol) search.set("symbol", params.symbol);
  if (params.limit !== undefined) search.set("limit", String(params.limit));
  if (params.offset !== undefined) search.set("offset", String(params.offset));
  const query = search.toString();
  return requestJson<TransactionPage>(
    `/portfolio/transactions${query ? `?${query}` : ""}`,
    {},
    fetchImpl,
  );
}

export function createTransaction(
  body: TransactionInput,
  fetchImpl: typeof fetch = fetch,
): Promise<Transaction> {
  return requestJson<Transaction>(
    "/portfolio/transactions",
    {
      method: "POST",
      body: JSON.stringify(body),
    },
    fetchImpl,
  );
}

export function getHoldings(
  fetchImpl: typeof fetch = fetch,
): Promise<HoldingsResponse> {
  return requestJson<HoldingsResponse>("/portfolio/holdings", {}, fetchImpl);
}

export function getAllocation(
  fetchImpl: typeof fetch = fetch,
): Promise<AllocationResponse> {
  return requestJson<AllocationResponse>(
    "/portfolio/allocation",
    {},
    fetchImpl,
  );
}

export type RiskLimits = {
  id: number;
  max_single_position_percent: string;
  max_sector_exposure_percent: string;
  min_cash_percent: string;
  max_portfolio_volatility_annual: string | null;
  max_drawdown_percent: string | null;
  rebalancing_threshold_percent: string;
  updated_at: string;
};

export type RiskBreach = {
  rule: string;
  severity: string;
  current_value: string;
  limit_value: string;
  message_en: string;
  message_ar: string;
  suggested_action_en: string;
  suggested_action_ar: string;
};

export type RiskReport = {
  total_portfolio_value: string;
  cash_percent: string;
  largest_position_symbol: string;
  largest_position_percent: string;
  sector_exposure: Record<string, string>;
  largest_sector: string;
  largest_sector_percent: string;
  annualized_volatility: string | null;
  max_drawdown: string | null;
  beta: string | null;
  sharpe_ratio: string | null;
  correlation_matrix: Record<string, Record<string, string | null>> | null;
  breaches: RiskBreach[];
  missing_data: string[];
  missing_data_ar: string[];
  data_as_of: string;
};

export type RiskSummary = {
  total_portfolio_value: string;
  cash_percent: string;
  largest_position_symbol: string;
  largest_position_percent: string;
  largest_sector: string;
  largest_sector_percent: string;
  breach_count: number;
  limits: {
    max_single_position_percent: string;
    max_sector_exposure_percent: string;
    min_cash_percent: string;
  };
  data_as_of: string;
};

export type RebalancingSuggestion = {
  symbol: string;
  action: string;
  action_ar: string;
  current_percent: string;
  target_percent: string;
  delta_shares_estimate: number | null;
  reason_en: string;
  reason_ar: string;
};

export function fetchRiskLimits(
  fetchImpl: typeof fetch = fetch,
): Promise<RiskLimits> {
  return requestJson<RiskLimits>("/api/settings/risk-limits", {}, fetchImpl);
}

export function updateRiskLimits(
  limits: Omit<RiskLimits, "id" | "updated_at">,
  fetchImpl: typeof fetch = fetch,
): Promise<RiskLimits> {
  return requestJson<RiskLimits>(
    "/api/settings/risk-limits",
    {
      method: "POST",
      body: JSON.stringify(limits),
    },
    fetchImpl,
  );
}

export function fetchRiskPortfolio(
  fetchImpl: typeof fetch = fetch,
): Promise<RiskReport> {
  return requestJson<RiskReport>("/api/risk/portfolio", {}, fetchImpl);
}

export function fetchRiskPortfolioSummary(
  fetchImpl: typeof fetch = fetch,
): Promise<RiskSummary> {
  return requestJson<RiskSummary>("/api/risk/portfolio/summary", {}, fetchImpl);
}

export function fetchRebalancingSuggestions(
  fetchImpl: typeof fetch = fetch,
): Promise<RebalancingSuggestion[]> {
  return requestJson<RebalancingSuggestion[]>(
    "/api/risk/portfolio/rebalancing",
    {},
    fetchImpl,
  );
}

export type PortfolioAnalysisInput = {
  include_portfolio_context: boolean;
  language: "en" | "ar";
};

export type PortfolioAnalysisResponse = {
  symbol: string | null;
  recommendation: string;
  confidence: number;
  valuation_assessment: string;
  fundamental_assessment: string;
  technical_assessment: string;
  portfolio_assessment: string;
  reasons: string[];
  reasons_ar: string[];
  risks: string[];
  risks_ar: string[];
  missing_information: string[];
  missing_information_ar: string[];
  data_as_of: string;
  sources: {
    source_type: string;
    title: string;
    title_ar: string | null;
    published_at: string | null;
    url: string | null;
  }[];
  interpretation: string | null;
  language: string;
};

export type WholePortfolioAnalysis = {
  overall_recommendation: string;
  overall_confidence: number;
  concentration_risk: string;
  sector_exposure: string;
  cash_position: string;
  holdings: {
    symbol: string;
    recommendation: string;
    confidence: number;
    weight: number;
    reasons: string[];
    reasons_ar: string[];
  }[];
  summary_en: string;
  summary_ar: string;
  data_as_of: string;
  sources: {
    source_type: string;
    title: string;
    title_ar: string | null;
    published_at: string | null;
    url: string | null;
  }[];
  missing_information: string[];
  missing_information_ar: string[];
};

export function analyzeStock(
  symbol: string,
  body: PortfolioAnalysisInput,
  fetchImpl: typeof fetch = fetch,
): Promise<PortfolioAnalysisResponse> {
  return requestJson<PortfolioAnalysisResponse>(
    `/api/analysis/stock/${encodeURIComponent(symbol)}`,
    {
      method: "POST",
      body: JSON.stringify(body),
    },
    fetchImpl,
  );
}

export function analyzePortfolio(
  body: { language: "en" | "ar" },
  fetchImpl: typeof fetch = fetch,
): Promise<WholePortfolioAnalysis> {
  return requestJson<WholePortfolioAnalysis>(
    "/api/analysis/portfolio",
    {
      method: "POST",
      body: JSON.stringify(body),
    },
    fetchImpl,
  );
}

export function deleteTransaction(
  id: string,
  fetchImpl: typeof fetch = fetch,
): Promise<void> {
  return requestJson<void>(
    `/portfolio/transactions/${encodeURIComponent(id)}`,
    {
      method: "DELETE",
    },
    fetchImpl,
  );
}
