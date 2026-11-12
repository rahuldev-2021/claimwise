import type { ReactNode } from "react";

export interface TabItem {
  id: string;
  label: string;
  panel: ReactNode;
}

export function Tabs({
  items,
  active,
  onChange,
}: {
  items: TabItem[];
  active: string;
  onChange: (id: string) => void;
}) {
  return (
    <div>
      <div className="flex flex-wrap gap-1 border-b border-border">
        {items.map((tab) => (
          <button
            key={tab.id}
            type="button"
            onClick={() => onChange(tab.id)}
            className={`rounded-t-md border border-b-0 px-2.5 py-1.5 text-[11px] font-medium transition ${
              active === tab.id
                ? "border-border-strong bg-base text-text"
                : "border-transparent text-text-muted hover:bg-surface-hover/60 hover:text-text"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>
      <div className="pt-2">{items.find((t) => t.id === active)?.panel}</div>
    </div>
  );
}
