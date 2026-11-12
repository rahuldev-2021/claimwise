import { X } from "lucide-react";
import { useEffect, useState } from "react";
import { createPortal } from "react-dom";

export type TextPreviewSection = {
  id: string;
  label: string;
  content: string;
  meta?: string;
};

type AssessmentTextPreviewModalProps = {
  open: boolean;
  title: string;
  subtitle?: string;
  sections: TextPreviewSection[];
  onClose: () => void;
};

export function AssessmentTextPreviewModal({
  open,
  title,
  subtitle,
  sections,
  onClose,
}: AssessmentTextPreviewModalProps) {
  const [activeId, setActiveId] = useState(sections[0]?.id ?? "");

  useEffect(() => {
    if (open && sections[0]) setActiveId(sections[0].id);
  }, [open, sections]);

  useEffect(() => {
    if (!open) return;
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") onClose();
    };
    window.document.addEventListener("keydown", onKey);
    const prev = window.document.body.style.overflow;
    window.document.body.style.overflow = "hidden";
    return () => {
      window.document.removeEventListener("keydown", onKey);
      window.document.body.style.overflow = prev;
    };
  }, [open, onClose]);

  if (!open || sections.length === 0) return null;

  const active = sections.find((section) => section.id === activeId) ?? sections[0];

  return createPortal(
    <div className="fixed inset-0 z-[95] flex items-center justify-center p-3 sm:p-6">
      <button type="button" className="absolute inset-0 bg-black/70" aria-label="Close preview" onClick={onClose} />
      <div className="relative flex h-[min(92vh,880px)] w-full max-w-5xl flex-col overflow-hidden rounded-xl border border-border bg-surface shadow-2xl">
        <header className="flex shrink-0 items-start justify-between gap-3 border-b border-border px-4 py-3 sm:px-5">
          <div className="min-w-0">
            <p className="text-[10px] font-semibold uppercase tracking-wide text-accent">Full preview</p>
            <h2 className="truncate text-[15px] font-semibold text-text">{title}</h2>
            {subtitle ? <p className="mt-0.5 text-[12px] text-text-muted">{subtitle}</p> : null}
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-md p-2 text-text-muted hover:bg-surface-hover hover:text-text"
            aria-label="Close"
          >
            <X className="h-4 w-4" />
          </button>
        </header>
        {sections.length > 1 ? (
          <div className="flex shrink-0 gap-1 overflow-x-auto border-b border-border px-4 py-2 scrollbar-thin">
            {sections.map((section) => (
              <button
                key={section.id}
                type="button"
                onClick={() => setActiveId(section.id)}
                className={`shrink-0 rounded-md px-3 py-1.5 text-[12px] font-medium transition ${
                  activeId === section.id
                    ? "bg-accent-muted text-accent"
                    : "text-text-muted hover:bg-surface-hover"
                }`}
              >
                {section.label}
              </button>
            ))}
          </div>
        ) : null}
        <div className="min-h-0 flex-1 overflow-y-auto p-4 scrollbar-thin sm:p-5">
          {active.meta ? <p className="mb-2 text-[11px] text-text-faint">{active.meta}</p> : null}
          <pre className="whitespace-pre-wrap break-words font-mono text-[12px] leading-relaxed text-text">
            {active.content || "(empty)"}
          </pre>
        </div>
      </div>
    </div>,
    window.document.body,
  );
}
