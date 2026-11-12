import { Link } from "react-router-dom";
import { Card } from "../components/ui/Card";

export function AdminDashboardPage() {
  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
        <p className="ui-label">Administration</p>
        <h1 className="text-[22px] font-semibold tracking-tight text-text">Admin panel</h1>
        <p className="text-[13px] text-text-muted">
          Organizations, dealer accounts, warranty agents, and audit logs — connected to Mongo auth
          APIs in the next backend increment.
        </p>
        </div>
        <Link
          to="/"
          className="inline-flex items-center rounded-lg border border-border bg-surface px-3 py-2 text-[13px] font-medium text-text transition hover:bg-surface-hover"
        >
          Back to home
        </Link>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <Card className="p-4">
          <h2 className="text-[13px] font-semibold text-text">Organizations</h2>
          <p className="mt-2 text-[13px] text-text-muted">Manufacturers and dealer service centres.</p>
        </Card>
        <Card className="p-4">
          <h2 className="text-[13px] font-semibold text-text">Users & roles</h2>
          <p className="mt-2 text-[13px] text-text-muted">
            Super Admin, Admin, Dealer Technician, Warranty Agent.
          </p>
        </Card>
        <Card className="p-4">
          <h2 className="text-[13px] font-semibold text-text">Claim statistics</h2>
          <p className="mt-2 text-[13px] text-text-muted">Cross-org metrics for authorized admins only.</p>
        </Card>
        <Card className="p-4">
          <h2 className="text-[13px] font-semibold text-text">Audit log</h2>
          <p className="mt-2 text-[13px] text-text-muted">Reviewer decisions and configuration changes.</p>
        </Card>
      </div>
    </div>
  );
}
