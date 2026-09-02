export type HealthResponse = {
  status: string;
  service: string;
  version: string;
  checks: Record<string, unknown>;
  timestamp: string;
  detail?: Record<string, string>;
};

export function getApiBaseUrl(): string {
  return process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000";
}

export async function fetchHealth(
  path: string,
  fetchImpl: typeof fetch = fetch,
): Promise<HealthResponse> {
  const response = await fetchImpl(`${getApiBaseUrl()}${path}`, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`API request failed: ${response.status}`);
  }
  return response.json() as Promise<HealthResponse>;
}

export function fetchLiveness(fetchImpl: typeof fetch = fetch): Promise<HealthResponse> {
  return fetchHealth("/health/live", fetchImpl);
}
