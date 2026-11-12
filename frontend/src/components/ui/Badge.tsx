import type { ReactNode } from "react";

const tones: Record<string, string> = {
  green: "border-status-ok/30 bg-status-ok/10 text-status-ok",
  amber: "border-status-warn/30 bg-status-warn/10 text-status-warn",
  red: "border-status-err/30 bg-status-err/10 text-status-err",
  slate: "border-border bg-surface-hover text-text-muted",
  blue: "border-primary/30 bg-primary/10 text-primary",
};

export function Badge({
  children,
  tone = "slate",
}: {
  children: ReactNode;
  tone?: keyof typeof tones;
}) {
  return (
    <span
      className={`inline-flex items-center rounded-md border px-2 py-0.5 text-[11px] font-medium ${tones[tone]}`}
    >
      {children}
    </span>
  );
}
