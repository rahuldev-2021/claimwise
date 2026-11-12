import { Monitor, Moon, Sun } from "lucide-react";
import type { ThemePreference } from "../lib/theme";
import { useTheme } from "./ThemeProvider";

const options: { id: ThemePreference; label: string; Icon: typeof Sun }[] = [
  { id: "system", label: "System", Icon: Monitor },
  { id: "dark", label: "Dark", Icon: Moon },
  { id: "light", label: "Light", Icon: Sun },
];

export function ThemeToggle() {
  const { preference, setPreference } = useTheme();

  return (
    <div className="flex rounded-lg border border-border bg-surface-raised p-0.5" role="group" aria-label="Theme">
      {options.map(({ id, label, Icon }) => {
        const active = preference === id;
        return (
          <button
            key={id}
            type="button"
            title={label}
            aria-label={label}
            aria-pressed={active}
            onClick={() => setPreference(id)}
            className={`flex items-center gap-1 rounded-md px-2 py-1 text-[12px] font-medium transition ${
              active
                ? "bg-surface-hover text-text ring-1 ring-border-strong"
                : "text-text-muted hover:text-text"
            }`}
          >
            <Icon className="h-3.5 w-3.5" aria-hidden />
            <span className="hidden sm:inline">{label}</span>
          </button>
        );
      })}
    </div>
  );
}
