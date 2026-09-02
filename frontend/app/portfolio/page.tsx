"use client";

import { useCallback, useEffect, useState } from "react";
import type { FormEvent } from "react";
import Link from "next/link";
import {
  AllocationResponse,
  ApiError,
  HoldingsResponse,
  Stock,
  TransactionInput,
  TransactionPage,
  createStock,
  createTransaction,
  getAllocation,
  getHoldings,
  listStocks,
  listTransactions,
} from "@/lib/api";
import { formatDate, formatMoney, formatPercent } from "@/lib/format";
import { direction } from "@/lib/locale";
import { normalizeLocale, t } from "@/lib/i18n";
import styles from "./page.module.css";

type TransactionForm = {
  type: TransactionInput["type"];
  symbol: string;
  quantity: string;
  price: string;
  fees: string;
  amount: string;
  executed_at: string;
};

const initialTransaction: TransactionForm = {
  type: "BUY",
  symbol: "",
  quantity: "",
  price: "",
  fees: "0",
  amount: "",
  executed_at: "",
};

function errorMessage(error: unknown): string {
  if (error instanceof ApiError) return `${error.code}: ${error.message}`;
  return "API unavailable";
}

export default function PortfolioPage() {
  const [locale, setLocale] = useState<"en" | "ar">("en");
  const [stocks, setStocks] = useState<Stock[]>([]);
  const [portfolio, setPortfolio] = useState<HoldingsResponse | null>(null);
  const [allocation, setAllocation] = useState<AllocationResponse | null>(null);
  const [transactions, setTransactions] = useState<TransactionPage | null>(null);
  const [loading, setLoading] = useState(true);
  const [networkError, setNetworkError] = useState(false);
  const [formError, setFormError] = useState("");
  const [stockSymbol, setStockSymbol] = useState("");
  const [stockName, setStockName] = useState("");
  const [stockNameAr, setStockNameAr] = useState("");
  const [stockSector, setStockSector] = useState("");
  const [transaction, setTransaction] = useState(initialTransaction);

  const label = (key: string) => t(locale, key);
  const money = (value: string | null) => (value === null ? "—" : formatMoney(value, locale));
  const numeric = (value: string | null) => (
    <span dir="ltr">{money(value)}</span>
  );

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const [stockData, holdingData, allocationData, transactionData] = await Promise.all([
        listStocks(),
        getHoldings(),
        getAllocation(),
        listTransactions({ limit: 20 }),
      ]);
      setStocks(stockData);
      setPortfolio(holdingData);
      setAllocation(allocationData);
      setTransactions(transactionData);
      setNetworkError(false);
    } catch (error) {
      setNetworkError(!(error instanceof ApiError));
      setFormError(errorMessage(error));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadData();
  }, [loadData]);

  useEffect(() => {
    setLocale(normalizeLocale(new URLSearchParams(window.location.search).get("lang") || "en"));
  }, []);

  async function submitStock(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setFormError("");
    try {
      await createStock({
        symbol: stockSymbol,
        name_en: stockName,
        name_ar: stockNameAr || null,
        sector: stockSector || null,
      });
      setStockSymbol("");
      setStockName("");
      setStockNameAr("");
      setStockSector("");
      await loadData();
    } catch (error) {
      setFormError(errorMessage(error));
    }
  }

  async function submitTransaction(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setFormError("");
    try {
      const payload: TransactionInput = {
        type: transaction.type,
        executed_at: new Date(transaction.executed_at).toISOString(),
      };
      if (transaction.type === "BUY" || transaction.type === "SELL") {
        payload.symbol = transaction.symbol;
        payload.quantity = transaction.quantity;
        payload.price = transaction.price;
        payload.fees = transaction.fees || "0";
      } else if (transaction.type === "DIVIDEND") {
        payload.symbol = transaction.symbol;
        payload.amount = transaction.amount;
      } else {
        payload.amount = transaction.amount;
      }
      await createTransaction(payload);
      setTransaction(initialTransaction);
      await loadData();
    } catch (error) {
      setFormError(errorMessage(error));
    }
  }

  function updateTransaction(field: keyof TransactionForm, value: string) {
    setTransaction((current) => ({ ...current, [field]: value }));
  }

  const typeNeedsStock = transaction.type === "BUY"
    || transaction.type === "SELL"
    || transaction.type === "DIVIDEND";
  const typeNeedsTradeFields = transaction.type === "BUY" || transaction.type === "SELL";

  if (networkError && !portfolio) {
    return (
      <main className={styles.page} lang={locale} dir={direction(locale)}>
        <div className={styles.shell}>
          <header className={styles.header}>
            <Link href="/">{label("EGX AI Portfolio Manager")}</Link>
            <a href={`/portfolio?lang=${locale === "ar" ? "en" : "ar"}`}>
              {label(locale === "ar" ? "Language: English" : "Language: Arabic")}
            </a>
          </header>
          <section className={styles.alert} role="alert">
            <h1>{label("API unavailable")}</h1>
            <p>{label("Start the backend and refresh the page.")}</p>
          </section>
        </div>
      </main>
    );
  }

  return (
    <main className={styles.page} lang={locale} dir={direction(locale)}>
      <div className={styles.shell}>
        <header className={styles.header}>
          <Link className={styles.brand} href="/">EGX AI Portfolio Manager</Link>
          <a href={`/portfolio?lang=${locale === "ar" ? "en" : "ar"}`}>
            {label(locale === "ar" ? "Language: English" : "Language: Arabic")}
          </a>
        </header>

        <div className={styles.titleRow}>
          <div>
            <p className={styles.eyebrow}>Phase 01</p>
            <h1>{label("Holdings")}</h1>
          </div>
          {portfolio && (
            <p className={styles.asOf}>
              {label("Data as of")}: <span dir="ltr">{formatDate(portfolio.data_as_of, locale)}</span>
            </p>
          )}
        </div>

        {formError && <p className={styles.formError} role="alert">{formError}</p>}
        {loading && <p className={styles.loading}>Loading…</p>}

        {portfolio && (
          <>
            <section className={styles.section}>
              <h2>{label("Summary")}</h2>
              <div className={styles.summaryGrid}>
                {[
                  [label("Cash"), portfolio.summary.cash],
                  [label("Total value"), portfolio.summary.total_value],
                  [label("Total cost"), portfolio.summary.total_cost],
                  [label("Unrealized P&L"), portfolio.summary.unrealized_pnl],
                  [label("Realized P&L"), portfolio.summary.realized_pnl],
                  [label("Unpriced count"), String(portfolio.summary.unpriced_count)],
                ].map(([name, value]) => (
                  <div className={styles.summaryCard} key={name}>
                    <span>{name}</span>
                    <strong>{name === label("Unpriced count") ? value : numeric(value)}</strong>
                  </div>
                ))}
              </div>
            </section>

            <section className={styles.section}>
              <h2>{label("Holdings")}</h2>
              <div className={styles.tableWrap}>
                <table>
                  <thead>
                    <tr>
                      <th>{label("Symbol")}</th>
                      <th>{label("Quantity")}</th>
                      <th>{label("Avg cost")}</th>
                      <th>{label("Price")}</th>
                      <th>{label("Market value")}</th>
                      <th>{label("Unrealized P&L")}</th>
                      <th>{label("Realized P&L")}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {portfolio.holdings.map((holding) => (
                      <tr key={holding.symbol}>
                        <td><strong>{holding.symbol}</strong></td>
                        <td>{numeric(holding.quantity)}</td>
                        <td>{numeric(holding.avg_cost)}</td>
                        <td>
                          {holding.price.status === "unavailable" ? (
                            <span className={styles.unavailable}>{label("Price unavailable")}</span>
                          ) : (
                            <span className={styles.priceCell}>
                              {numeric(holding.price.value)}
                              <small>
                                <span className={`${styles.badge} ${styles[holding.price.status]}`}>
                                  {label(holding.price.status === "fresh" ? "Fresh" : "Stale")}
                                </span>
                                {holding.price.source} · {formatDate(holding.price.observed_at, locale)}
                              </small>
                            </span>
                          )}
                        </td>
                        <td>{numeric(holding.market_value)}</td>
                        <td>{numeric(holding.unrealized_pnl)}</td>
                        <td>{numeric(holding.realized_pnl)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>
          </>
        )}

        {allocation && (
          <section className={styles.section}>
            <h2>{label("Allocation")}</h2>
            <div className={styles.tableWrap}>
              <table>
                <thead>
                  <tr><th>{label("Symbol")}</th><th>{label("Sector")}</th><th>{label("Market value")}</th><th>{label("Weight")}</th></tr>
                </thead>
                <tbody>
                  {allocation.by_symbol.map((line) => (
                    <tr key={`symbol-${line.name}`}><td>{line.name}</td><td>{label("Holdings")}</td><td>{numeric(line.value)}</td><td><span dir="ltr">{formatPercent(line.weight, locale)}%</span></td></tr>
                  ))}
                  {allocation.by_sector.map((line) => (
                    <tr key={`sector-${line.name}`}><td>{line.name}</td><td>{label("Sector")}</td><td>{numeric(line.value)}</td><td><span dir="ltr">{formatPercent(line.weight, locale)}%</span></td></tr>
                  ))}
                  <tr><td>{allocation.cash.name}</td><td>{label("Cash")}</td><td>{numeric(allocation.cash.value)}</td><td><span dir="ltr">{formatPercent(allocation.cash.weight, locale)}%</span></td></tr>
                </tbody>
              </table>
            </div>
          </section>
        )}

        {transactions && (
          <section className={styles.section}>
            <h2>{label("Transactions")}</h2>
            <div className={styles.tableWrap}>
              <table>
                <thead>
                  <tr><th>{label("Type")}</th><th>{label("Symbol")}</th><th>{label("Quantity")}</th><th>{label("Amount")}</th><th>{label("Executed at")}</th></tr>
                </thead>
                <tbody>
                  {[...transactions.items].reverse().map((item) => (
                    <tr key={item.id}>
                      <td><strong>{item.type}</strong></td>
                      <td>{item.symbol || "—"}</td>
                      <td>{numeric(item.quantity)}</td>
                      <td>{numeric(item.amount || item.price)}</td>
                      <td><span dir="ltr">{formatDate(item.executed_at, locale)}</span></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        )}

        <div className={styles.forms}>
          <section className={styles.section}>
            <h2>{label("Add stock")}</h2>
            <form onSubmit={submitStock} className={styles.form}>
              <label>{label("Symbol")}<input required value={stockSymbol} onChange={(event) => setStockSymbol(event.target.value)} /></label>
              <label>{label("Name (English)")}<input required value={stockName} onChange={(event) => setStockName(event.target.value)} /></label>
              <label>{label("Name (Arabic)")}<input value={stockNameAr} onChange={(event) => setStockNameAr(event.target.value)} /></label>
              <label>{label("Sector")}<input value={stockSector} onChange={(event) => setStockSector(event.target.value)} /></label>
              <button type="submit">{label("Submit")}</button>
            </form>
          </section>

          <section className={styles.section}>
            <h2>{label("Add transaction")}</h2>
            <form onSubmit={submitTransaction} className={styles.form}>
              <label>{label("Type")}
                <select value={transaction.type} onChange={(event) => updateTransaction("type", event.target.value)}>
                  <option value="BUY">BUY</option>
                  <option value="SELL">SELL</option>
                  <option value="DEPOSIT">DEPOSIT</option>
                  <option value="WITHDRAWAL">WITHDRAWAL</option>
                  <option value="DIVIDEND">DIVIDEND</option>
                </select>
              </label>
              {typeNeedsStock && (
                <label>{label("Symbol")}
                  <input required value={transaction.symbol} list="portfolio-stocks" onChange={(event) => updateTransaction("symbol", event.target.value)} />
                  <datalist id="portfolio-stocks">{stocks.map((stock) => <option key={stock.symbol} value={stock.symbol} />)}</datalist>
                </label>
              )}
              {typeNeedsTradeFields && (
                <>
                  <label>{label("Quantity")}<input required type="number" step="0.0001" min="0" value={transaction.quantity} onChange={(event) => updateTransaction("quantity", event.target.value)} /></label>
                  <label>{label("Price")}<input required type="number" step="0.0001" min="0" value={transaction.price} onChange={(event) => updateTransaction("price", event.target.value)} /></label>
                  <label>{label("Fees")}<input type="number" step="0.01" min="0" value={transaction.fees} onChange={(event) => updateTransaction("fees", event.target.value)} /></label>
                </>
              )}
              {(transaction.type === "DEPOSIT" || transaction.type === "WITHDRAWAL" || transaction.type === "DIVIDEND") && (
                <label>{label("Amount")}<input required type="number" step="0.01" min="0" value={transaction.amount} onChange={(event) => updateTransaction("amount", event.target.value)} /></label>
              )}
              <label>{label("Executed at")}<input required type="datetime-local" value={transaction.executed_at} onChange={(event) => updateTransaction("executed_at", event.target.value)} /></label>
              <button type="submit">{label("Submit")}</button>
            </form>
          </section>
        </div>
      </div>
    </main>
  );
}
