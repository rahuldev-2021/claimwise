export type ThemePreference = "system" | "light" | "dark";

const STORAGE_KEY = "claimwise-theme";

export function getStoredTheme(): ThemePreference {
  const v = localStorage.getItem(STORAGE_KEY);
  if (v === "light" || v === "dark" || v === "system") return v;
  return "dark";
}

export function setStoredTheme(pref: ThemePreference): void {
  localStorage.setItem(STORAGE_KEY, pref);
}

export function resolveIsDark(pref: ThemePreference): boolean {
  if (pref === "dark") return true;
  if (pref === "light") return false;
  return window.matchMedia("(prefers-color-scheme: dark)").matches;
}

export function applyTheme(pref: ThemePreference): void {
  const root = document.documentElement;
  if (resolveIsDark(pref)) {
    root.classList.add("dark");
  } else {
    root.classList.remove("dark");
  }
}
