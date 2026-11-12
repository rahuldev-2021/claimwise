export type AppRole =
  | "super_admin"
  | "admin"
  | "warranty_agent"
  | "dealer_technician"
  | "developer"
  | "customer"
  | "unknown";

const ROLE_PRIORITY: AppRole[] = [
  "super_admin",
  "admin",
  "warranty_agent",
  "dealer_technician",
  "developer",
  "customer",
];

export function primaryRole(roles: string[] | undefined): AppRole {
  if (!roles?.length) return "unknown";
  for (const r of ROLE_PRIORITY) {
    if (roles.includes(r)) return r;
  }
  return "unknown";
}

export function isDealerRole(role: AppRole): boolean {
  return role === "dealer_technician" || role === "customer";
}

export function isReviewerRole(role: AppRole): boolean {
  return role === "warranty_agent" || role === "developer";
}

export function isAdminRole(role: AppRole): boolean {
  return role === "admin" || role === "super_admin";
}

export function roleLabel(role: AppRole): string {
  const labels: Record<AppRole, string> = {
    super_admin: "Super Admin",
    admin: "Admin",
    warranty_agent: "Claim reviewer",
    dealer_technician: "Dealer Technician",
    developer: "Developer",
    customer: "Customer",
    unknown: "User",
  };
  return labels[role];
}
