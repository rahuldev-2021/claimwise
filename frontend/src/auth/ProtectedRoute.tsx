import { Navigate, Outlet, useLocation } from "react-router-dom";
import { useAuth } from "./AuthProvider";

/** Auth gate — must render `<Outlet />` so child routes (AppShell, pages) mount. */
export function ProtectedRoute() {
  const { user, loading } = useAuth();
  const location = useLocation();

  if (loading) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center gap-2 bg-base px-4 text-center text-[13px] text-text-muted">
        <p>Loading session…</p>
        <p className="max-w-sm text-[11px] text-text-faint">
          Stuck here? Start the backend on port 8000 (python main.py in backend), then refresh.
        </p>
      </div>
    );
  }

  if (!user) {
    return (
      <Navigate
        to="/login"
        replace
        state={{ from: location.pathname + location.search }}
      />
    );
  }

  return <Outlet />;
}
