"use client";

import { useCallback, useEffect, useState } from "react";
import type { FormEvent } from "react";
import Link from "next/link";
import { ApiError, RiskLimits, fetchRiskLimits, updateRiskLimits } from "@/lib/api";
import { direction } from "@/lib/locale";
import { normalizeLocale, t } from "@/lib/i18n";
import styles from "../portfolio/page.module.css";

function errorMessage(error: unknown): string {
  if (error instanceof ApiError) return `${error.code}: ${error.message}`;
  return "API unavailable";
}

export default function SettingsPage() {
  const [locale, setLocale] = useState<"en" | "ar">("en");
  const [limits, setLimits] = useState<RiskLimits | null>(null);
  const [form, setForm] = useState({
    max_single_position_percent: "25",
    max_sector_exposure_percent: "40",
    min_cash_percent: "10",
    rebalancing_threshold_percent: "5",
  });
  const [error, setError] = useState("");
  const [saved, setSaved] = useState(false);

  const label = (key: string) => t(locale, key);

  useEffect(() => {
    setLocale(normalizeLocale(new URLSearchParams(window.location.search).get("lang") || "en"));
  }, []);

  useEffect(() => {
    document.documentElement.lang = locale;
    document.documentElement.dir = direction(locale);
  }, [locale]);

  const load = useCallback(async () => {
    try {
      const data = await fetchRiskLimits();
      setLimits(data);
      setForm({
        max_single_position_percent: data.max_single_position_percent,
        max_sector_exposure_percent: data.max_sector_exposure_percent,
        min_cash_percent: data.min_cash_percent,
        rebalancing_threshold_percent: data.rebalancing_threshold_percent,
      });
    } catch (err) {
      setError(errorMessage(err));
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setSaved(false);
    try {
      await updateRiskLimits({
        max_single_position_percent: form.max_single_position_percent,
        max_sector_exposure_percent: form.max_sector_exposure_percent,
        min_cash_percent: form.min_cash_percent,
        max_portfolio_volatility_annual: null,
        max_drawdown_percent: null,
        rebalancing_threshold_percent: form.rebalancing_threshold_percent,
      });
      setSaved(true);
      await load();
    } catch (err) {
      setError(errorMessage(err));
    }
  }

  return (
    <main className={styles.page} lang={locale} dir={direction(locale)}>
      <div className={styles.shell}>
        <header className={styles.header}>
          <Link className={styles.brand} href={`/?lang=${locale}`}>EGX AI Portfolio Manager</Link>
          <a href={`/settings?lang=${locale === "ar" ? "en" : "ar"}`}>
            {label(locale === "ar" ? "Language: English" : "Language: Arabic")}
          </a>
        </header>

        <div className={styles.titleRow}>
          <h1>{label("Settings")}</h1>
        </div>

        {error && <p className={styles.formError} role="alert">{error}</p>}
        {saved && <p className={styles.loading} role="status">{label("Saved")}</p>}

        {limits && (
          <section className={styles.section}>
            <h2>{label("Risk limits")}</h2>
            <form onSubmit={submit} className={styles.form}>
              <label>{label("Max single position")}
                <input type="number" step="0.01" min="0" max="100" required value={form.max_single_position_percent} onChange={(e) => setForm({ ...form, max_single_position_percent: e.target.value })} />
              </label>
              <label>{label("Max sector exposure")}
                <input type="number" step="0.01" min="0" max="100" required value={form.max_sector_exposure_percent} onChange={(e) => setForm({ ...form, max_sector_exposure_percent: e.target.value })} />
              </label>
              <label>{label("Min cash")}
                <input type="number" step="0.01" min="0" max="100" required value={form.min_cash_percent} onChange={(e) => setForm({ ...form, min_cash_percent: e.target.value })} />
              </label>
              <label>{label("Rebalancing threshold")}
                <input type="number" step="0.01" min="0" max="100" required value={form.rebalancing_threshold_percent} onChange={(e) => setForm({ ...form, rebalancing_threshold_percent: e.target.value })} />
              </label>
              <button type="submit">{label("Save")}</button>
            </form>
          </section>
        )}
      </div>
    </main>
  );
}
