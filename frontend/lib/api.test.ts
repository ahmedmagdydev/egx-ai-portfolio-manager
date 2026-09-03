import { describe, expect, it } from "vitest";
import { ApiError, fetchLiveness, getHoldings, isApiUnavailable } from "./api";

describe("fetchLiveness", () => {
  it("returns the API health response", async () => {
    const fetchImpl = async () =>
      new Response(JSON.stringify({
        status: "ok",
        service: "egx-api",
        version: "0.0.1",
        checks: {},
        timestamp: "2025-01-01T00:00:00Z",
      }), { status: 200 });
    await expect(fetchLiveness(fetchImpl as typeof fetch)).resolves.toMatchObject({
      status: "ok",
      service: "egx-api",
    });
  });

  it("rejects unavailable responses", async () => {
    const fetchImpl = async () => new Response("offline", { status: 503 });
    await expect(fetchLiveness(fetchImpl as typeof fetch)).rejects.toThrow("503");
  });

  it("loads typed holdings", async () => {
    const fetchImpl = async () =>
      new Response(JSON.stringify({
        holdings: [],
        summary: { cash: "100.00" },
        data_as_of: null,
        currency: "EGP",
        generated_at: "2025-01-01T00:00:00Z",
      }), { status: 200 });
    await expect(getHoldings(fetchImpl as typeof fetch)).resolves.toMatchObject({
      currency: "EGP",
      holdings: [],
    });
  });

  it("parses backend errors into ApiError", async () => {
    const fetchImpl = async () =>
      new Response(JSON.stringify({
        code: "INSUFFICIENT_CASH",
        message: "Insufficient cash",
        details: { held: "1.00" },
      }), { status: 422 });
    const result = getHoldings(fetchImpl as typeof fetch);
    await expect(result).rejects.toMatchObject({
      name: "ApiError",
      code: "INSUFFICIENT_CASH",
      message: "Insufficient cash",
    } satisfies Partial<ApiError>);
    await expect(result.catch((error: unknown) => isApiUnavailable(error))).resolves.toBe(false);
  });

  it("recognizes a non-JSON server failure as API unavailable", async () => {
    const fetchImpl = async () => new Response("<html>offline</html>", {
      status: 500,
      headers: { "Content-Type": "text/html" },
    });
    const result = getHoldings(fetchImpl as typeof fetch);
    await expect(result).rejects.toMatchObject({ code: "HTTP_ERROR", status: 500 });
    await expect(result.catch((error: unknown) => isApiUnavailable(error))).resolves.toBe(true);
  });
});
