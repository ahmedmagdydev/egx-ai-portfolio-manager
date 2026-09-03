import { describe, it, expect } from "vitest";
import arLabels from "./labels/ar.json";
import arRiskLabels from "./labels/ar-risk.json";

describe("Arabic labels", () => {
  it("maps every recommendation to Arabic", () => {
    expect(arLabels.recommendations.BUY).toBe("شراء");
    expect(arLabels.recommendations.SELL).toBe("بيع");
    expect(arLabels.recommendations.HOLD).toBe("احتفاظ");
    expect(arLabels.recommendations.ACCUMULATE).toBe("تراكم");
    expect(arLabels.recommendations.REDUCE).toBe("تقليل");
    expect(arLabels.recommendations.WATCH).toBe("مراقبة");
  });

  it("uses EGP currency symbol", () => {
    expect(arLabels.currency).toBe("ج.م");
  });

  it("uses DD/MM/YYYY date format", () => {
    expect(arLabels.dateFormat).toBe("DD/MM/YYYY");
  });
});

describe("Arabic risk labels", () => {
  it("maps risk terminology to Arabic", () => {
    expect(arRiskLabels.position_concentration).toBe("تركيز المركز");
    expect(arRiskLabels.sector_exposure).toBe("تعرض القطاع");
    expect(arRiskLabels.cash_percentage).toBe("نسبة النقد");
    expect(arRiskLabels.portfolio_volatility).toBe("تقلب المحفظة");
    expect(arRiskLabels.maximum_drawdown).toBe("أقصى انخفاض");
    expect(arRiskLabels.beta).toBe("بيتا");
    expect(arRiskLabels.sharpe_ratio).toBe("نسبة شارب");
    expect(arRiskLabels.correlation).toBe("الارتباط");
  });

  it("maps severity labels", () => {
    expect(arRiskLabels.critical).toBe("خطر");
    expect(arRiskLabels.warning).toBe("تنبيه");
  });
});
