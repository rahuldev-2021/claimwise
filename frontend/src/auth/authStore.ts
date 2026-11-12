/** In-memory access token only — never persisted to localStorage. */

let accessToken: string | null = null;
let refreshPromise: Promise<string | null> | null = null;

export function getAccessToken(): string | null {
  return accessToken;
}

export function setAccessToken(token: string | null): void {
  accessToken = token;
}

export function getRefreshPromise(): Promise<string | null> | null {
  return refreshPromise;
}

export function setRefreshPromise(p: Promise<string | null> | null): void {
  refreshPromise = p;
}

export function clearAuthSession(): void {
  accessToken = null;
  refreshPromise = null;
}
