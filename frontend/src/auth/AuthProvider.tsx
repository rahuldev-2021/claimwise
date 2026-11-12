import { useCallback, useEffect, useMemo, useState, type ReactNode } from "react";
import { clearAuthSession, getAccessToken, setAccessToken } from "./authStore";
import { fetchMe, login as apiLogin, logout as apiLogout, refreshAccessToken } from "../api/auth";
import { AuthContext, type AuthContextValue } from "./authContext";
import type { AuthUser } from "./types";

export type { AuthUser } from "./types";
export { useAuth } from "./useAuth";

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [loading, setLoading] = useState(true);

  const hydrate = useCallback(async () => {
    try {
      const token = await refreshAccessToken();
      if (!token) {
        setUser(null);
        return;
      }
      const me = await fetchMe();
      setUser(me);
    } catch {
      clearAuthSession();
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void hydrate();
  }, [hydrate]);

  const login = useCallback(async (email: string, password: string) => {
    const { access_token } = await apiLogin(email, password);
    setAccessToken(access_token);
    const me = await fetchMe();
    setUser(me);
  }, []);

  const logout = useCallback(async () => {
    await apiLogout();
    clearAuthSession();
    setUser(null);
  }, []);

  const hasPermission = useCallback(
    (permission: string) => Boolean(user?.permissions.includes(permission)),
    [user],
  );

  const isAdmin = useMemo(
    () => Boolean(user?.roles.some((r) => r === "admin" || r === "super_admin")),
    [user],
  );

  const value = useMemo<AuthContextValue>(
    () => ({ user, loading, login, logout, hasPermission, isAdmin }),
    [user, loading, login, logout, hasPermission, isAdmin],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function authHeader(): Record<string, string> {
  const token = getAccessToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}
