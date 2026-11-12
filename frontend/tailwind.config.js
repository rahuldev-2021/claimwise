/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  darkMode: "class",
  theme: {
    extend: {
      fontFamily: {
        sans: [
          "Inter",
          "Segoe UI",
          "system-ui",
          "-apple-system",
          "Roboto",
          "Helvetica",
          "Arial",
          "sans-serif",
        ],
      },
      colors: {
        base: "rgb(var(--color-base) / <alpha-value>)",
        "base-deep": "rgb(var(--color-base-deep) / <alpha-value>)",
        sidebar: "rgb(var(--color-sidebar) / <alpha-value>)",
        surface: "rgb(var(--color-surface) / <alpha-value>)",
        "surface-raised": "rgb(var(--color-surface-raised) / <alpha-value>)",
        "surface-hover": "rgb(var(--color-surface-hover) / <alpha-value>)",
        bubble: {
          user: "rgb(var(--color-user-bubble) / <alpha-value>)",
        },
        text: {
          DEFAULT: "rgb(var(--color-text) / <alpha-value>)",
          muted: "rgb(var(--color-text-muted) / <alpha-value>)",
          faint: "rgb(var(--color-text-faint) / <alpha-value>)",
        },
        accent: {
          DEFAULT: "rgb(var(--color-accent) / <alpha-value>)",
          hover: "rgb(var(--color-accent-hover) / <alpha-value>)",
          fg: "rgb(var(--color-accent-fg) / <alpha-value>)",
          muted: "rgb(var(--color-accent-muted) / <alpha-value>)",
        },
        primary: {
          DEFAULT: "rgb(var(--color-primary) / <alpha-value>)",
          hover: "rgb(var(--color-primary-hover) / <alpha-value>)",
          fg: "rgb(var(--color-primary-fg) / <alpha-value>)",
        },
        brand: {
          DEFAULT: "rgb(var(--color-brand) / <alpha-value>)",
          hover: "rgb(var(--color-brand-hover) / <alpha-value>)",
          fg: "rgb(var(--color-brand-fg) / <alpha-value>)",
        },
        "status-ok": "rgb(var(--color-status-ok) / <alpha-value>)",
        "status-warn": "rgb(var(--color-status-warn) / <alpha-value>)",
        "status-err": "rgb(var(--color-status-err) / <alpha-value>)",
        border: {
          DEFAULT: "var(--border)",
          strong: "var(--border-strong)",
        },
      },
      boxShadow: {
        composer: "var(--shadow-composer)",
        glow: "var(--shadow-glow)",
      },
      width: {
        sidebar: "168px",
        "sidebar-collapsed": "48px",
        sources: "340px",
      },
      maxWidth: {
        content: "768px",
      },
    },
  },
  plugins: [],
};
