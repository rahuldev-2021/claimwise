import { createContext, useContext, useEffect, useMemo, useState } from "react";
import {
  applyTheme,
  getStoredTheme,
  setStoredTheme,
  type ThemePreference,
} from "../lib/theme";

const ThemeContext = createContext<{
  preference: ThemePreference;
  setPreference: (p: ThemePreference) => void;
} | null>(null);

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [preference, setPreferenceState] = useState<ThemePreference>(() => getStoredTheme());

  const setPreference = (p: ThemePreference) => {
    setStoredTheme(p);
    setPreferenceState(p);
    applyTheme(p);
  };

  useEffect(() => {
    applyTheme(preference);
    if (preference !== "system") return;
    const mq = window.matchMedia("(prefers-color-scheme: dark)");
    const onChange = () => applyTheme("system");
    mq.addEventListener("change", onChange);
    return () => mq.removeEventListener("change", onChange);
  }, [preference]);

  const value = useMemo(() => ({ preference, setPreference }), [preference]);

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
}

export function useTheme() {
  const ctx = useContext(ThemeContext);
  if (!ctx) throw new Error("useTheme must be used within ThemeProvider");
  return ctx;
}
