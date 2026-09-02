import { describe, expect, it } from "vitest";
import { normalizeLocale, t } from "./i18n";

describe("i18n", () => {
  it("falls back to English for unknown locales and keys", () => {
    expect(normalizeLocale("fr")).toBe("en");
    expect(t("fr", "Holdings")).toBe("Holdings");
    expect(t("en", "Unknown label")).toBe("Unknown label");
  });
});
