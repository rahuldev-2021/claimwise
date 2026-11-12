import { useLayoutEffect, useState, type CSSProperties, type ReactNode, type RefObject } from "react";
import { createPortal } from "react-dom";

type Align = "left" | "right";

export function AnchoredDropdown({
  open,
  anchorRef,
  align = "right",
  widthClass = "w-56",
  children,
  className = "",
}: {
  open: boolean;
  anchorRef: RefObject<HTMLElement | null>;
  align?: Align;
  widthClass?: string;
  children: ReactNode;
  className?: string;
}) {
  const [style, setStyle] = useState<CSSProperties>({ visibility: "hidden" });

  useLayoutEffect(() => {
    if (!open) return;
    const el = anchorRef.current;
    if (!el) return;

    const update = () => {
      const rect = el.getBoundingClientRect();
      const top = rect.bottom + 4;
      const base: CSSProperties = {
        position: "fixed",
        top,
        zIndex: 90,
        visibility: "visible",
      };
      if (align === "right") {
        setStyle({ ...base, right: Math.max(8, window.innerWidth - rect.right) });
      } else {
        setStyle({ ...base, left: Math.max(8, rect.left) });
      }
    };

    update();
    window.addEventListener("resize", update);
    window.addEventListener("scroll", update, true);
    return () => {
      window.removeEventListener("resize", update);
      window.removeEventListener("scroll", update, true);
    };
  }, [open, anchorRef, align]);

  if (!open) return null;

  return createPortal(
    <div
      data-role="anchored-dropdown"
      style={style}
      className={`rounded-lg border border-border bg-surface py-1 shadow-composer ${widthClass} ${className}`}
    >
      {children}
    </div>,
    document.body,
  );
}

export function isAnchoredDropdownTarget(target: EventTarget | null): boolean {
  return target instanceof Element && Boolean(target.closest('[data-role="anchored-dropdown"]'));
}
