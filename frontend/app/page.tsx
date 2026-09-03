"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { direction } from "@/lib/locale";
import { normalizeLocale, t } from "@/lib/i18n";
import styles from "./page.module.css";

const nav = [
  { href: "/portfolio", key: "Holdings" },
  { href: "/risk", key: "Risk" },
  { href: "/analysis", key: "Analysis" },
  { href: "/settings", key: "Settings" },
];

export default function Home() {
  const [locale, setLocale] = useState<"en" | "ar">("en");

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

  const label = (key: string) => t(locale, key);

  return (
    <main className={styles.page} lang={locale} dir={direction(locale)}>
      <div className={styles.shell}>
        <h1>EGX AI Portfolio Manager</h1>
        <p>{label("Dashboard")}</p>
        <nav className={styles.nav}>
          {nav.map((item) => (
            <Link
              key={item.href}
              href={`${item.href}?lang=${locale}`}
              className={styles.card}
            >
              {label(item.key)}
            </Link>
          ))}
        </nav>
      </div>
    </main>
  );
}
