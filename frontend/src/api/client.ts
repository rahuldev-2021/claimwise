import { getAccessToken } from "../auth/authStore";
import { apiCredentialsDefault, getApiBaseUrl } from "../lib/apiConfig";
import { refreshAccessToken } from "./auth";

const DEFAULT_TIMEOUT_MS = 120_000;

export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public body?: unknown,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

export async function apiFetch<T>(
  path: string,
  options: RequestInit & { timeoutMs?: number; skipAuthRetry?: boolean } = {},
): Promise<T> {
  const { timeoutMs = DEFAULT_TIMEOUT_MS, skipAuthRetry = false, ...init } = options;
  const url = `${getApiBaseUrl()}${path}`;
  const credentials = init.credentials ?? apiCredentialsDefault();
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);

  const token = getAccessToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(init.headers as Record<string, string> | undefined),
  };
  if (token && !headers.Authorization) {
    headers.Authorization = `Bearer ${token}`;
  }

  try {
    let response = await fetch(url, {
      ...init,
      signal: controller.signal,
      credentials,
      headers,
    });

    if (
      response.status === 401 &&
      !skipAuthRetry &&
      path !== "/api/auth/login" &&
      path !== "/api/auth/refresh"
    ) {
      const newToken = await refreshAccessToken();
      if (newToken) {
        headers.Authorization = `Bearer ${newToken}`;
        response = await fetch(url, {
          ...init,
          signal: controller.signal,
          credentials,
          headers,
        });
      }
    }

    if (response.status === 204) {
      return undefined as T;
    }

    const text = await response.text();
    let data: unknown = undefined;
    if (text) {
      try {
        data = JSON.parse(text) as unknown;
      } catch {
        data = text;
      }
    }
    if (!response.ok) {
      const detail =
        typeof data === "object" && data !== null && "detail" in data
          ? String((data as { detail: unknown }).detail)
          : response.statusText;
      throw new ApiError(detail || `HTTP ${response.status}`, response.status, data);
    }
    return data as T;
  } catch (err) {
    if (err instanceof ApiError) throw err;
    if (err instanceof Error && err.name === "AbortError") {
      throw new ApiError("Request timed out", 408);
    }
    throw new ApiError(err instanceof Error ? err.message : "Network error", 0);
  } finally {
    clearTimeout(timer);
  }
}
