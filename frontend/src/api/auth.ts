import { ApiError, apiFetch } from "./client";
import {
  clearAuthSession,
  getAccessToken,
  getRefreshPromise,
  setAccessToken,
  setRefreshPromise,
} from "../auth/authStore";
import type { AuthUser } from "../auth/AuthProvider";

type TokenResponse = { access_token: string; expires_in: number; token_type: string };

export async function login(email: string, password: string): Promise<TokenResponse> {
  return apiFetch<TokenResponse>("/api/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
    credentials: "include",
  });
}

export async function refreshAccessToken(): Promise<string | null> {
  const existing = getRefreshPromise();
  if (existing) return existing;

  const promise = (async () => {
    try {
      const data = await apiFetch<TokenResponse>("/api/auth/refresh", {
        method: "POST",
        credentials: "include",
        body: JSON.stringify({}),
        skipAuthRetry: true,
      });
      setAccessToken(data.access_token);
      return data.access_token;
    } catch {
      clearAuthSession();
      return null;
    } finally {
      setRefreshPromise(null);
    }
  })();

  setRefreshPromise(promise);
  return promise;
}

export async function fetchMe(): Promise<AuthUser> {
  const token = getAccessToken();
  if (!token) throw new ApiError("Not authenticated", 401);
  return apiFetch<AuthUser>("/api/auth/me", {
    credentials: "include",
    headers: { Authorization: `Bearer ${token}` },
  });
}

export async function logout(): Promise<void> {
  await apiFetch<void>("/api/auth/logout", {
    method: "POST",
    credentials: "include",
  });
}
