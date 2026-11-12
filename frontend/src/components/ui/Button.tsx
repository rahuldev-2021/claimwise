import type { ButtonHTMLAttributes, ReactNode } from "react";

export function Button({
  children,
  variant = "primary",
  className = "",
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & {
  children: ReactNode;
  variant?: "primary" | "secondary" | "ghost";
}) {
  const base =
    "inline-flex items-center justify-center rounded-lg px-3 py-2 text-[13px] font-medium transition focus:outline-none focus:ring-2 focus:ring-accent/15 disabled:cursor-not-wait disabled:opacity-50";
  const variants = {
    primary: "bg-accent text-accent-fg hover:bg-accent-hover",
    secondary: "border border-border bg-surface text-text hover:bg-surface-hover",
    ghost: "text-text-muted hover:bg-surface-hover",
  };
  return (
    <button className={`${base} ${variants[variant]} ${className}`} {...props}>
      {children}
    </button>
  );
}
