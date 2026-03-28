import { BrowserRouter, Routes, Route, Navigate, useNavigate, useParams } from "react-router-dom";
import { useAuth } from "./app/auth";
import { WizardProvider } from "./app/WizardProvider";

// Layouts
import AdminLayout from "./layouts/AdminLayout";
import ArtistLayout from "./layouts/ArtistLayout";

// Auth / Gate
import LoginPage from "./pages/LoginPage";
import RegisterPage from "./pages/RegisterPage";
import ProtectedRoute from "./components/ProtectedRoute";
import UsersListPage from "./pages/admin/UsersListPage";
import UserDetailPage from "./pages/admin/UserDetailPage";
import ContractsPage from "./pages/admin/ContractsPage";
import ContractPage from "./pages/artist/ContractPage";
import EarningsPage from "./pages/artist/EarningsPage";
import RoyaltiesPage from "./pages/admin/RoyaltiesPage";

// Admin pages (existing)
import Dashboard from "./pages/Dashboard";
import SandboxMonitor from "./pages/SandboxMonitor";
import AnalyticsDashboard from "./pages/AnalyticsDashboard";
import AutomationCenter from "./pages/AutomationCenter";
import ValidationCenter from "./pages/ValidationCenter";
import ReleaseDetail from "./pages/ReleaseDetail";
import ReleaseWizard from "./pages/ReleaseWizard";

// Artist pages (new)
import ArtistDashboard from "./pages/artist/ArtistDashboard";
import ArtistProfile from "./pages/artist/ArtistProfile";

// ─────────────────────────────────────────────────────────────────
// Root redirect: sends unauthenticated users to /login, others to
// their role's home page.
// ─────────────────────────────────────────────────────────────────
function RootRedirect() {
  const { user, isAuthenticated } = useAuth();
  if (!isAuthenticated) return <Navigate to="/login" replace />;
  return <Navigate to={user?.role === "admin" ? "/admin" : "/artist"} replace />;
}

// ─────────────────────────────────────────────────────────────────
// Admin dashboard wrapper — keeps the wizard-based navigation that
// Dashboard currently relies on (onNewRelease / onOpenRelease).
// ─────────────────────────────────────────────────────────────────
function AdminDashboardPage() {
  const navigate = useNavigate();
  return (
    <Dashboard
      onNewRelease={() => navigate("/admin/wizard")}
      onOpenRelease={(id) => navigate(`/admin/releases/${id}`)}
    />
  );
}

function AdminWizardPage() {
  const navigate = useNavigate();
  return (
    <WizardProvider>
      <ReleaseWizard onFinish={() => navigate("/admin")} />
    </WizardProvider>
  );
}

function AdminReleaseDetailPage() {
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  if (!id) return <Navigate to="/admin" replace />;
  return <ReleaseDetail releaseId={id} onBack={() => navigate("/admin")} />;
}

function AdminValidationPage() {
  const navigate = useNavigate();
  return (
    <ValidationCenter
      onOpenRelease={(id) => navigate(`/admin/releases/${id}`)}
    />
  );
}

function ArtistWizardPage() {
  const navigate = useNavigate();
  return (
    <WizardProvider>
      <ReleaseWizard onFinish={() => navigate("/artist")} />
    </WizardProvider>
  );
}

// ─────────────────────────────────────────────────────────────────
// App
// ─────────────────────────────────────────────────────────────────
export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Root */}
        <Route path="/" element={<RootRedirect />} />

        {/* Login */}
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route
          path="/artist/contract"
          element={
            <ProtectedRoute requiredRole="artist">
              <ContractPage />
            </ProtectedRoute>
          }
        />

        {/* ── Admin area ─────────────────────────────────────── */}
        <Route
          path="/admin"
          element={
            <ProtectedRoute requiredRole="admin">
              <AdminLayout />
            </ProtectedRoute>
          }
        >
          <Route index element={<AdminDashboardPage />} />
          <Route path="releases" element={<AdminDashboardPage />} />
          <Route path="releases/:id" element={<AdminReleaseDetailPage />} />
          <Route path="wizard" element={<AdminWizardPage />} />
          <Route path="sandbox" element={<SandboxMonitor />} />
          <Route path="analytics" element={<AnalyticsDashboard />} />
          <Route path="automation" element={<AutomationCenter />} />
          <Route path="validation" element={<AdminValidationPage />} />
          <Route path="royalties" element={<RoyaltiesPage />} />
          {/* delivery — served by Dashboard deliveries tab */}
          <Route path="delivery" element={<AdminDashboardPage />} />
          {/* artists — served by Dashboard catalog tab */}
          <Route path="artists" element={<AdminDashboardPage />} />
          <Route path="users" element={<UsersListPage />} />
          <Route path="users/:id" element={<UserDetailPage />} />
          <Route path="contracts" element={<ContractsPage />} />
        </Route>

        {/* ── Artist portal ─────────────────────────────────── */}
        <Route
          path="/artist"
          element={
            <ProtectedRoute requiredRole="artist">
              <ArtistLayout />
            </ProtectedRoute>
          }
        >
          <Route index element={<ArtistDashboard />} />
          <Route path="new" element={<ArtistWizardPage />} />
          <Route path="earnings" element={<EarningsPage />} />
          <Route path="analytics" element={<AnalyticsDashboard />} />
          <Route path="profile" element={<ArtistProfile />} />
        </Route>

        {/* Fallback */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
