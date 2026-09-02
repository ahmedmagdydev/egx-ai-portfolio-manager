export function direction(locale: string): "rtl" | "ltr" {
  return locale.toLowerCase().startsWith("ar") ? "rtl" : "ltr";
}
