import { Moon, Sun } from "lucide-react";
import { resolveIsDark } from "../lib/theme";
import { useTheme } from "./ThemeProvider";

/** Lucius-style control: single sun/moon icon toggles light and dark (no segment labels). */
export function ThemeToggleIcon() {
  const { preference, setPreference } = useTheme();
  const isDark = resolveIsDark(preference);
  const Icon = isDark ? Sun : Moon;

  return (
    <button
      type="button"
      className="rounded-lg p-2 text-text-muted transition hover:bg-surface-hover hover:text-text"
      aria-label={isDark ? "Switch to light theme" : "Switch to dark theme"}
      title={isDark ? "Light" : "Dark"}
      onClick={() => setPreference(isDark ? "light" : "dark")}
    >
      <Icon className="h-4 w-4" aria-hidden />
    </button>
  );
}
