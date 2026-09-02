import { describe, expect, it } from "vitest";
import { fetchLiveness } from "./api";

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
});
