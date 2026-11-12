/** API origin from Vite env (`VITE_API_BASE_URL`). Empty = same origin (dev proxy). */
export function getApiBaseUrl(): string {
  const raw = import.meta.env.VITE_API_BASE_URL as string | undefined;
  if (!raw?.trim()) return "";
  return raw.trim().replace(/\/$/, "");
}

export function apiCredentialsDefault(): RequestCredentials {
  return getApiBaseUrl() ? "include" : "same-origin";
}
