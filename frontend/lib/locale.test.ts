import { describe, expect, it } from "vitest";
import { direction } from "./locale";

describe("direction", () => {
  it("uses RTL for Arabic", () => {
    expect(direction("ar")).toBe("rtl");
    expect(direction("ar-EG")).toBe("rtl");
  });

  it("uses LTR by default", () => {
    expect(direction("en")).toBe("ltr");
  });
});
