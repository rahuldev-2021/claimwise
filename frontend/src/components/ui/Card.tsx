import type { ReactNode } from "react";

export function Card({
  title,
  children,
  className = "",
}: {
  title?: string;
  children: ReactNode;
  className?: string;
}) {
  return (
    <section className={`rounded-lg border border-border bg-surface ${className}`}>
      {title ? (
        <header className="border-b border-border px-4 py-3">
          <h2 className="text-[13px] font-semibold text-text">{title}</h2>
        </header>
      ) : null}
      <div className="p-4">{children}</div>
    </section>
  );
}
