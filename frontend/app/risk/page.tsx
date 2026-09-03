"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { RiskReport, fetchRiskPortfolio, isApiUnavailable } from "@/lib/api";
import { direction } from "@/lib/locale";
import { normalizeLocale, t } from "@/lib/i18n";
import { formatDate, formatMoney, formatPercent } from "@/lib/format";
import styles from "../portfolio/page.module.css";

export default function RiskPage() {
  const [locale, setLocale] = useState<"en" | "ar">("en");
  const [report, setReport] = useState<RiskReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const label = useCallback((key: string) => t(locale, key), [locale]);

  useEffect(() => {
    setLocale(
      normalizeLocale(
        new URLSearchParams(window.location.search).get("lang") || "en",
      ),
    );
  }, []);

  useEffect(() => {
    document.documentElement.lang = locale;
    document.documentElement.dir = direction(locale);
  }, [locale]);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const data = await fetchRiskPortfolio();
      setReport(data);
      setError("");
    } catch (err) {
      setError(isApiUnavailable(err) ? label("API unavailable") : String(err));
    } finally {
      setLoading(false);
    }
  }, [label]);

  useEffect(() => {
    void load();
  }, [load]);

  const severityClass = (severity: string) =>
    severity === "CRITICAL" ? styles.unavailable : styles.stale;

  return (
    <main className={styles.page} lang={locale} dir={direction(locale)}>
      <div className={styles.shell}>
        <header className={styles.header}>
          <Link className={styles.brand} href={`/?lang=${locale}`}>
            EGX AI Portfolio Manager
          </Link>
          <a href={`/risk?lang=${locale === "ar" ? "en" : "ar"}`}>
            {label(locale === "ar" ? "Language: English" : "Language: Arabic")}
          </a>
        </header>

        <div className={styles.titleRow}>
          <h1>{label("Risk")}</h1>
          {report && (
            <p className={styles.asOf}>
              {label("Data as of")}:{" "}
              <span dir="ltr">{formatDate(report.data_as_of, locale)}</span>
            </p>
          )}
        </div>

        {error && (
          <p className={styles.formError} role="alert">
            {error}
          </p>
        )}
        {loading && <p className={styles.loading}>Loading…</p>}

        {report && (
          <>
            <section className={styles.section}>
              <h2>{label("Risk report")}</h2>
              <div className={styles.summaryGrid}>
                <div className={styles.summaryCard}>
                  <span>{label("Total value")}</span>
                  <strong>
                    <span dir="ltr">
                      {formatMoney(report.total_portfolio_value, locale)}
                    </span>
                  </strong>
                </div>
                <div className={styles.summaryCard}>
                  <span>{label("Cash")}</span>
                  <strong>
                    <span dir="ltr">
                      {formatPercent(report.cash_percent, locale)}%
                    </span>
                  </strong>
                </div>
                <div className={styles.summaryCard}>
                  <span>{label("Max single position")}</span>
                  <strong>{report.largest_position_symbol || "—"}</strong>
                </div>
              </div>
            </section>

            <section className={styles.section}>
              <h2>{label("Breaches")}</h2>
              {report.breaches.length === 0 ? (
                <p>{label("No breaches")}</p>
              ) : (
                <ul className={styles.list}>
                  {report.breaches.map((breach) => (
                    <li
                      key={breach.rule}
                      className={`${styles.badge} ${severityClass(breach.severity)}`}
                    >
                      <strong>{breach.rule}</strong>
                      <p>
                        {locale === "ar"
                          ? breach.message_ar
                          : breach.message_en}
                      </p>
                      <p>
                        {locale === "ar"
                          ? breach.suggested_action_ar
                          : breach.suggested_action_en}
                      </p>
                    </li>
                  ))}
                </ul>
              )}
            </section>
          </>
        )}
      </div>
    </main>
  );
}
