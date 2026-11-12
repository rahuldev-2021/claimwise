import { Navigate, Route, Routes } from "react-router-dom";
import { ProtectedRoute } from "./auth/ProtectedRoute";
import { AppShell } from "./layouts/AppShell";
import { AdminDashboardPage } from "./pages/AdminDashboardPage";
import { AdminUsersPage } from "./pages/AdminUsersPage";
import { ClaimDetailRoute } from "./pages/ClaimDetailRoute";
import { ClaimSubmitPage } from "./pages/ClaimSubmitPage";
import { ClaimsListPage } from "./pages/ClaimsListPage";
import { DealerDashboardPage } from "./pages/DealerDashboardPage";
import { LoginPage } from "./pages/LoginPage";
import { SectionPlaceholderPage } from "./pages/SectionPlaceholderPage";
import { SettingsPage } from "./pages/SettingsPage";

export function AppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/" element={<ProtectedRoute />}>
        <Route element={<AppShell />}>
          <Route index element={<DealerDashboardPage />} />
          <Route path="claims/new" element={<ClaimSubmitPage />} />
          <Route path="claims" element={<ClaimsListPage />} />
          <Route path="claims/:claimId" element={<ClaimDetailRoute />} />
          <Route path="settings" element={<SettingsPage />} />
          <Route path="admin" element={<AdminDashboardPage />} />
          <Route path="admin/users" element={<AdminUsersPage />} />
          <Route
            path="admin/organizations"
            element={
              <SectionPlaceholderPage
                title="Organizations"
                description="Manage manufacturer and dealer organizations (Mongo admin APIs — Phase 7B)."
              />
            }
          />
          <Route
            path="admin/audit"
            element={
              <SectionPlaceholderPage
                title="Audit logs"
                description="Reviewer decisions and configuration changes will be listed here."
              />
            }
          />
          <Route path="dealer/dashboard" element={<Navigate to="/" replace />} />
          <Route path="dealer/claims/new" element={<Navigate to="/claims/new" replace />} />
          <Route path="claims/all" element={<Navigate to="/claims" replace />} />
          <Route path="dashboard" element={<Navigate to="/" replace />} />
        </Route>
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
