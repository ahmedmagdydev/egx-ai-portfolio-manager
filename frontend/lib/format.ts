export function formatMoney(value: string, locale: string): string {
  return new Intl.NumberFormat(locale, { minimumFractionDigits: 2 }).format(Number(value));
}

export function formatPercent(value: string, locale: string): string {
  return new Intl.NumberFormat(locale, { maximumFractionDigits: 2, minimumFractionDigits: 2 }).format(
    Number(value) * 100,
  );
}

export function formatDate(value: string | null, locale: string): string {
  if (!value) return "—";
  return new Intl.DateTimeFormat(locale, { dateStyle: "medium", timeStyle: "short" }).format(
    new Date(value),
  );
}
