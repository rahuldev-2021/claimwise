import { Search } from "lucide-react";
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { ThemeToggleIcon } from "./ThemeToggleIcon";

export function AppHeader() {
  const [q, setQ] = useState("");
  const navigate = useNavigate();

  const onSearch = (e: React.FormEvent) => {
    e.preventDefault();
    const needle = q.trim();
    navigate(needle ? `/claims?q=${encodeURIComponent(needle)}` : "/claims");
  };

  return (
    <header className="shrink-0 border-b border-border bg-surface px-4 py-2 pl-12 lg:pl-4">
      <div className="flex items-center gap-2">
        <form onSubmit={onSearch} className="relative min-w-0 flex-1">
          <Search className="pointer-events-none absolute left-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-text-faint" />
          <input
            type="search"
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="Search claims, VIN…"
            className="ui-input w-full max-w-xl rounded-lg border-border bg-base-deep/80 py-2 pl-8 pr-3 text-[13px] dark:bg-base-deep"
          />
        </form>
        <ThemeToggleIcon />
      </div>
    </header>
  );
}
