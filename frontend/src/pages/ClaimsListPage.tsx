import { useQuery } from "@tanstack/react-query";
import { Search, SlidersHorizontal } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { listClaims } from "../api/services";
import type { ClaimStatus } from "../api/types/claim";
import { ClaimsTable } from "../features/claims/ClaimsTable";
import { ErrorState, LoadingState } from "../components/ui/StateMessage";
import { dealerCopy } from "../lib/dealerCopy";

export function ClaimsListPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [q, setQ] = useState(searchParams.get("q") ?? "");
  const [showFilters, setShowFilters] = useState(false);

  useEffect(() => {
    setQ(searchParams.get("q") ?? "");
  }, [searchParams]);

  useEffect(() => {
    if (searchParams.get("status") === "under_review") {
      const next = new URLSearchParams(searchParams);
      next.delete("status");
      setSearchParams(next, { replace: true });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps -- strip legacy review-queue query once
  }, []);

  const [status, setStatus] = useState<ClaimStatus | "">("");
  const [category, setCategory] = useState("");
  const [make, setMake] = useState("");

  const query = useQuery({
    queryKey: ["claims", { q, status, category }],
    queryFn: () =>
      listClaims({
        q: q.trim() || undefined,
        status: status || undefined,
        repair_category: category.trim() || undefined,
        sort: "submission_date_desc",
      }),
  });

  const filtered = useMemo(() => {
    let rows = query.data ?? [];
    if (make.trim()) {
      const needle = make.trim().toLowerCase();
      rows = rows.filter((c) => c.vehicle.make.toLowerCase().includes(needle));
    }
    return rows;
  }, [query.data, make]);

  const applySearch = () => {
    const next = new URLSearchParams(searchParams);
    if (q.trim()) next.set("q", q.trim());
    else next.delete("q");
    setSearchParams(next, { replace: true });
  };

  return (
    <div className="mx-auto w-full max-w-6xl space-y-2">
      <section className="overflow-hidden rounded-xl border border-border bg-surface shadow-composer">
        <div className="flex flex-wrap items-center gap-2 border-b border-border bg-surface-raised/40 px-3 py-2">
          <h1 className="shrink-0 text-[15px] font-semibold tracking-tight text-text">
            {dealerCopy.list.myClaims}
          </h1>
          {!query.isLoading && !query.error ? (
            <span className="shrink-0 text-[11px] text-text-faint">
              <span className="font-semibold tabular-nums text-text-muted">{filtered.length}</span>{" "}
              {filtered.length === 1 ? "claim" : "claims"}
            </span>
          ) : null}
          <div className="flex min-w-[12rem] flex-1 items-center gap-1.5 sm:min-w-0 sm:pl-2">
            <Search className="h-3.5 w-3.5 shrink-0 text-text-faint" strokeWidth={1.75} />
            <input
              className="min-w-0 flex-1 bg-transparent py-0.5 text-[12px] text-text placeholder:text-text-faint focus:outline-none"
              placeholder="Search by claim ID…"
              value={q}
              onChange={(e) => setQ(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") applySearch();
              }}
            />
            <button
              type="button"
              onClick={applySearch}
              className="shrink-0 rounded-md bg-primary px-2.5 py-1 text-[11px] font-medium text-primary-fg hover:bg-primary-hover"
            >
              Search
            </button>
          </div>
          <button
            type="button"
            onClick={() => setShowFilters((v) => !v)}
            className={`inline-flex shrink-0 items-center gap-1 rounded-md border px-2 py-1 text-[11px] font-medium transition ${
              showFilters
                ? "border-border-strong bg-surface-raised text-text"
                : "border-border text-text-muted hover:bg-surface-hover"
            }`}
          >
            <SlidersHorizontal className="h-3 w-3" strokeWidth={1.75} />
            Filters
          </button>
        </div>

        {showFilters ? (
          <div className="grid gap-2 border-b border-border bg-base-deep/20 px-3 py-2 sm:grid-cols-3">
            <label className="block">
              <span className="mb-0.5 block text-[10px] font-medium text-text-faint">Status</span>
              <select
                className="ui-input w-full py-1.5 text-[12px]"
                value={status}
                onChange={(e) => setStatus(e.target.value as ClaimStatus | "")}
              >
                <option value="">All statuses</option>
                <option value="SUBMITTED">Submitted</option>
                <option value="UNDER_REVIEW">Under review</option>
                <option value="PENDING_INFORMATION">Pending information</option>
                <option value="COMPLETED">Completed</option>
                <option value="CLOSED">Closed</option>
              </select>
            </label>
            <label className="block">
              <span className="mb-0.5 block text-[10px] font-medium text-text-faint">Repair category</span>
              <input
                className="ui-input w-full py-1.5 text-[12px]"
                placeholder="e.g. ENGINE"
                value={category}
                onChange={(e) => setCategory(e.target.value)}
              />
            </label>
            <label className="block">
              <span className="mb-0.5 block text-[10px] font-medium text-text-faint">Vehicle make</span>
              <input
                className="ui-input w-full py-1.5 text-[12px]"
                placeholder="e.g. Ford"
                value={make}
                onChange={(e) => setMake(e.target.value)}
              />
            </label>
          </div>
        ) : null}

        {query.isLoading ? (
          <div className="px-3 py-4">
            <LoadingState />
          </div>
        ) : null}
        {query.error ? (
          <div className="px-3 py-4">
            <ErrorState message={(query.error as Error).message} />
          </div>
        ) : null}
        {!query.isLoading && !query.error ? <ClaimsTable claims={filtered} /> : null}
      </section>
    </div>
  );
}
