export function formatDate(iso: string): string {
  try {
    return new Intl.DateTimeFormat(undefined, {
      dateStyle: "medium",
      timeStyle: "short",
    }).format(new Date(iso));
  } catch {
    return iso;
  }
}

export function formatMoney(amount: string, currency: string): string {
  try {
    return new Intl.NumberFormat(undefined, {
      style: "currency",
      currency: currency || "USD",
    }).format(Number(amount));
  } catch {
    return `${amount} ${currency}`;
  }
}

export function formatScore(value: number | null | undefined, digits = 2): string {
  if (value == null || Number.isNaN(value)) return "—";
  return value.toFixed(digits);
}

export function formatPercent(value: string | number | null | undefined, digits = 1): string {
  if (value == null || value === "") return "—";
  const n = typeof value === "string" ? Number.parseFloat(value) : value;
  if (Number.isNaN(n)) return "—";
  const sign = n > 0 ? "+" : "";
  return `${sign}${n.toFixed(digits)}%`;
}
