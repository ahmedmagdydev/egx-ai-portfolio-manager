"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { direction } from "@/lib/locale";
import { normalizeLocale, t } from "@/lib/i18n";
import styles from "../portfolio/page.module.css";

export default function AnalysisPage() {
  const [locale, setLocale] = useState<"en" | "ar">("en");

  useEffect(() => {
    setLocale(normalizeLocale(new URLSearchParams(window.location.search).get("lang") || "en"));
  }, []);

  useEffect(() => {
    document.documentElement.lang = locale;
    document.documentElement.dir = direction(locale);
  }, [locale]);

  const label = (key: string) => t(locale, key);

  return (
    <main className={styles.page} lang={locale} dir={direction(locale)}>
      <div className={styles.shell}>
        <header className={styles.header}>
          <Link className={styles.brand} href={`/?lang=${locale}`}>EGX AI Portfolio Manager</Link>
          <a href={`/analysis?lang=${locale === "ar" ? "en" : "ar"}`}>
            {label(locale === "ar" ? "Language: English" : "Language: Arabic")}
          </a>
        </header>
        <div className={styles.titleRow}>
          <h1>{label("Analysis")}</h1>
        </div>
        <section className={styles.section}>
          <p>Stock and portfolio analysis UI will be added in a future iteration.</p>
        </section>
      </div>
    </main>
  );
}
