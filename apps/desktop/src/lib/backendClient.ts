import type { BackendSnapshot, HealthResponse, StatusResponse } from "./types";

const API_BASE = import.meta.env.VITE_SLON_API_BASE ?? "/api";

async function readJson<T>(path: string): Promise<{ status: number; body: T | null }> {
  const response = await fetch(`${API_BASE}${path}`, {
    method: "GET",
    headers: { Accept: "application/json" },
  });

  let body: T | null = null;
  const text = await response.text();
  if (text.trim().length > 0) {
    body = JSON.parse(text) as T;
  }
  return { status: response.status, body };
}

export async function getHealth(): Promise<HealthResponse> {
  const result = await readJson<HealthResponse>("/health");
  if (result.status < 200 || result.status >= 300 || result.body === null) {
    throw new Error(`health rejected with ${result.status}`);
  }
  return result.body;
}

export async function getStatus(): Promise<{ statusCode: number; body: StatusResponse | null }> {
  const result = await readJson<StatusResponse>("/status");
  return { statusCode: result.status, body: result.body };
}

export async function readBackendSnapshot(): Promise<BackendSnapshot> {
  const checkedAt = new Date().toISOString();

  try {
    const health = await getHealth();
    const status = await getStatus();

    if (status.statusCode === 401 || status.statusCode === 403) {
      return {
        state: "unauthorized",
        health,
        status: null,
        message: "Backend is reachable. Pairing or auth is required for status.",
        checkedAt,
      };
    }

    if (status.statusCode >= 200 && status.statusCode < 300) {
      return {
        state: "connected",
        health,
        status: status.body,
        message: "Local backend connected.",
        checkedAt,
      };
    }

    return {
      state: "error",
      health,
      status: status.body,
      message: `Status endpoint rejected with ${status.statusCode}.`,
      checkedAt,
    };
  } catch (error) {
    return {
      state: "offline",
      health: null,
      status: null,
      message: error instanceof Error ? error.message : "Local backend is offline.",
      checkedAt,
    };
  }
}