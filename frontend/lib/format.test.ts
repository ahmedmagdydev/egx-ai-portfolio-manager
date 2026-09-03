import { describe, expect, it } from "vitest";
import { formatMoney, formatPercent } from "./format";

describe("formatMoney", () => {
  it("formats English currency-like values", () => {
    expect(formatMoney("1234.5", "en")).toContain("1,234.50");
  });

  it("formats Arabic digits for Arabic locale", () => {
    expect(formatMoney("1234.5", "ar")).toContain("١٬٢٣٤٫٥٠");
  });

  it("renders allocation ratios as percentages", () => {
    expect(formatPercent("0.110473", "en")).toBe("11.05");
  });
});
