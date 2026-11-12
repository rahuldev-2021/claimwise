import { Car, ChevronLeft, ChevronRight, Menu, X } from "lucide-react";
import { useState } from "react";
import { Link, Outlet, useLocation } from "react-router-dom";
import { AppHeader } from "../components/AppHeader";
import { UserAccountMenu } from "../components/UserAccountMenu";
import { useDealerClaimStats } from "../hooks/useDealerClaimStats";
import { appNavSections, type NavItem } from "../lib/navConfig";
import { isNavItemActive } from "../lib/navActive";

function navClass(isActive: boolean, collapsed: boolean) {
  return `flex w-full items-center rounded-md transition ${
    collapsed ? "justify-center p-2" : "gap-2 px-2 py-1.5"
  } text-[12px] ${
    isActive
      ? "bg-surface-raised font-medium text-text shadow-composer"
      : "text-text-muted hover:bg-surface-hover/50 hover:text-text"
  }`;
}

export function AppShell() {
  const location = useLocation();
  const dealerStats = useDealerClaimStats();

  const sections = appNavSections({
    myClaimsCount: dealerStats.data?.total,
  });

  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  const sidebarWidth = collapsed ? "w-sidebar-collapsed" : "w-sidebar";
  const isHome = location.pathname === "/";
  const isNewClaim = location.pathname === "/claims/new";
  const isClaimsList = location.pathname === "/claims";
  const investigationLayout = /^\/claims\/[^/]+/.test(location.pathname) && !isNewClaim;

  const sidebarInner = (
    <>
      <Link
        to="/"
        className={`mt-1 flex items-center rounded-md transition hover:bg-surface-hover/50 ${
          collapsed ? "justify-center p-2" : "gap-2 px-2 py-2"
        }`}
        title="CLAIMWISE Home"
        onClick={() => setMobileOpen(false)}
      >
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md bg-surface ring-1 ring-border">
          <Car className="h-4 w-4 text-primary" strokeWidth={1.5} aria-hidden />
        </div>
        {!collapsed && (
          <p className="truncate text-[12px] font-semibold tracking-tight text-text">CLAIMWISE</p>
        )}
      </Link>

      <nav className="scrollbar-thin flex-1 space-y-1 overflow-y-auto px-2 pt-3">
        {sections.map((section, si) => (
          <div key={section.title ?? `nav-${si}`} className="space-y-0.5">
            {section.items.map((item: NavItem) => {
              const active = isNavItemActive(location.pathname, location.search, item);
              return (
                <Link
                  key={item.to + item.label}
                  to={item.to}
                  className={navClass(active, collapsed)}
                  title={item.label}
                  onClick={() => setMobileOpen(false)}
                >
                  <item.icon
                    className={`h-4 w-4 shrink-0 ${active ? "text-text" : "opacity-70"}`}
                    strokeWidth={1.75}
                  />
                  {!collapsed && <span className="flex-1 truncate">{item.label}</span>}
                  {!collapsed && item.badge != null && item.badge > 0 ? (
                    <span className="min-w-[1.25rem] rounded bg-surface-hover px-1 py-0.5 text-center text-[9px] font-semibold tabular-nums text-text-muted">
                      {item.badge}
                    </span>
                  ) : null}
                </Link>
              );
            })}
          </div>
        ))}
      </nav>

      <footer className="relative z-20 shrink-0 overflow-visible border-t border-border px-1.5 py-2">
        {collapsed && (
          <button
            type="button"
            className="mb-1 flex w-full justify-center rounded-md p-1 text-text-muted hover:bg-surface-hover"
            aria-label="Expand sidebar"
            onClick={() => setCollapsed(false)}
          >
            <ChevronRight className="h-3.5 w-3.5" />
          </button>
        )}
        <UserAccountMenu collapsed={collapsed} />
      </footer>
    </>
  );

  return (
    <div className="flex h-screen overflow-hidden bg-base">
      {mobileOpen && (
        <button
          type="button"
          className="fixed inset-0 z-40 bg-black/60 lg:hidden"
          aria-label="Close menu"
          onClick={() => setMobileOpen(false)}
        />
      )}

      <aside
        className={`fixed inset-y-0 left-0 z-50 flex flex-col overflow-visible border-r border-border bg-sidebar transition-[width] duration-200 lg:static lg:z-auto ${sidebarWidth} ${
          mobileOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0"
        }`}
      >
        <div className="flex items-center justify-end px-1 pt-1 lg:hidden">
          <button
            type="button"
            className="rounded-md p-1 text-text-muted hover:bg-surface-hover"
            aria-label="Close sidebar"
            onClick={() => setMobileOpen(false)}
          >
            <X className="h-4 w-4" />
          </button>
        </div>
        {sidebarInner}
        {!collapsed && (
          <button
            type="button"
            className="absolute -right-2.5 top-12 hidden h-5 w-5 items-center justify-center rounded-full border border-border bg-surface text-text-muted shadow-composer hover:bg-surface-hover lg:flex"
            aria-label="Collapse sidebar"
            onClick={() => setCollapsed(true)}
          >
            <ChevronLeft className="h-3 w-3" />
          </button>
        )}
      </aside>

      <div className="relative flex min-w-0 flex-1 flex-col overflow-hidden">
        {!isHome && !isClaimsList ? (
          <div className="relative shrink-0">
            <button
              type="button"
              className="absolute left-2 top-2 z-10 rounded-md p-1.5 text-text-muted hover:bg-surface-hover lg:hidden"
              aria-label="Open menu"
              onClick={() => setMobileOpen(true)}
            >
              <Menu className="h-4 w-4" />
            </button>
            <AppHeader />
          </div>
        ) : (
          <button
            type="button"
            className="absolute left-2 top-2 z-20 rounded-md p-1.5 text-text-muted hover:bg-surface-hover lg:hidden"
            aria-label="Open menu"
            onClick={() => setMobileOpen(true)}
          >
            <Menu className="h-4 w-4" />
          </button>
        )}

        <main
          className={`scrollbar-thin min-h-0 flex-1 ${
            isHome ? "overflow-y-auto overflow-x-hidden" : "overflow-y-auto"
          } ${
            isHome
              ? "p-0"
              : isClaimsList
                ? "p-2 pt-10 md:p-3 md:pt-3"
                : isNewClaim
                  ? "p-3 md:p-4"
                  : investigationLayout
                    ? "p-2 md:p-3"
                    : "p-4 md:p-6"
          }`}
        >
          <div
            className={
              isHome
                ? "h-full min-h-0"
                : isClaimsList
                  ? "mx-auto w-full max-w-6xl animate-slide-up"
                  : isNewClaim
                    ? "mx-auto w-full max-w-5xl animate-slide-up"
                    : investigationLayout
                      ? "mx-auto max-w-[1400px] animate-slide-up"
                      : "mx-auto max-w-6xl animate-slide-up"
            }
          >
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
}
