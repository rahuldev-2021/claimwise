import { createContext } from "react";
import type { AuthUser } from "./types";

export type AuthContextValue = {
  user: AuthUser | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  hasPermission: (permission: string) => boolean;
  isAdmin: boolean;
};

export const AuthContext = createContext<AuthContextValue | null>(null);
