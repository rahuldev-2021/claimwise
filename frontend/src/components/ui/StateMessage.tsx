export function LoadingState({ label = "Loading…" }: { label?: string }) {
  return (
    <p className="text-[13px] text-text-muted" role="status">
      {label}
    </p>
  );
}

export function ErrorState({ message }: { message: string }) {
  return (
    <div
      className="rounded-lg border border-status-err/30 bg-status-err/10 p-4 text-[13px] text-status-err"
      role="alert"
    >
      {message}
    </div>
  );
}

export function EmptyState({ message }: { message: string }) {
  return <p className="text-[13px] text-text-faint">{message}</p>;
}
