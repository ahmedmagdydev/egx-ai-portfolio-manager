const dictionary = {
  en: {
    Holdings: "Holdings",
    Allocation: "Allocation",
    Transactions: "Transactions",
    "Add stock": "Add stock",
    "Add transaction": "Add transaction",
    Symbol: "Symbol",
    Quantity: "Quantity",
    Price: "Price",
    Fees: "Fees",
    Amount: "Amount",
    Type: "Type",
    "Executed at": "Executed at",
    Cash: "Cash",
    "Market value": "Market value",
    "Avg cost": "Avg cost",
    "Unrealized P&L": "Unrealized P&L",
    "Realized P&L": "Realized P&L",
    Weight: "Weight",
    Sector: "Sector",
    "Price unavailable": "Price unavailable",
    Stale: "Stale",
    Fresh: "Fresh",
    "Data as of": "Data as of",
    Source: "Source",
    "API unavailable": "API unavailable",
    Submit: "Submit",
    Summary: "Summary",
    "Total value": "Total value",
    "Total cost": "Total cost",
    "Unpriced count": "Unpriced count",
    "Language: Arabic": "العربية",
    "Language: English": "English",
    "Name (English)": "Name (English)",
    "Name (Arabic)": "Name (Arabic)",
    "Start the backend and refresh the page.": "Start the backend and refresh the page.",
  },
  ar: {
    Holdings: "الممتلكات",
    Allocation: "التوزيع",
    Transactions: "المعاملات",
    "Add stock": "إضافة سهم",
    "Add transaction": "إضافة معاملة",
    Symbol: "الرمز",
    Quantity: "الكمية",
    Price: "السعر",
    Fees: "الرسوم",
    Amount: "المبلغ",
    Type: "النوع",
    "Executed at": "تاريخ التنفيذ",
    Cash: "النقدية",
    "Market value": "القيمة السوقية",
    "Avg cost": "متوسط التكلفة",
    "Unrealized P&L": "الربح أو الخسارة غير المحققة",
    "Realized P&L": "الربح أو الخسارة المحققة",
    Weight: "الوزن",
    Sector: "القطاع",
    "Price unavailable": "السعر غير متاح",
    Stale: "قديم",
    Fresh: "حديث",
    "Data as of": "البيانات حتى",
    Source: "المصدر",
    "API unavailable": "واجهة البرمجة غير متاحة",
    Submit: "إرسال",
    Summary: "الملخص",
    "Total value": "إجمالي القيمة",
    "Total cost": "إجمالي التكلفة",
    "Unpriced count": "عدد الأسعار غير المتاحة",
    "Language: Arabic": "العربية",
    "Language: English": "English",
    "Name (English)": "الاسم بالإنجليزية",
    "Name (Arabic)": "الاسم بالعربية",
    "Start the backend and refresh the page.": "ابدأ الخادم ثم حدّث الصفحة.",
  },
} as const;

export type Locale = keyof typeof dictionary;
export type TranslationKey = keyof typeof dictionary.en;

export function normalizeLocale(locale: string): Locale {
  return locale === "ar" ? "ar" : "en";
}

export function t(locale: string, key: string): string {
  const selected = dictionary[normalizeLocale(locale)];
  if (key in selected) return selected[key as TranslationKey];
  return dictionary.en[key as TranslationKey] || key;
}
