import { useState } from 'react';
import { WizardProvider } from './app/WizardProvider';
import ReleaseWizard from './pages/ReleaseWizard';
import Dashboard from './pages/Dashboard';
import AppShell from './components/layout/AppShell';
import ReleaseDetail from './pages/ReleaseDetail';
import SandboxMonitor from './pages/SandboxMonitor';
import AnalyticsDashboard from './pages/AnalyticsDashboard';
import AutomationCenter from './pages/AutomationCenter';
import ValidationCenter from './pages/ValidationCenter';
import AuthGateway from './pages/AuthGateway';
import { clearAuthSession, getUserId, getUserRole, type UserRole } from './app/auth';

function App() {
  const [currentPage, setCurrentPage] = useState<'wizard' | 'dashboard' | 'releaseDetail' | 'sandbox' | 'analytics' | 'automation' | 'validation'>('dashboard');
  const [activeReleaseId, setActiveReleaseId] = useState<string | null>(null);
  const [authVersion, setAuthVersion] = useState(0);

  const role = (getUserRole() || null) as UserRole | null;
  const userId = getUserId() || undefined;

  // Ensure a tenant is always set (required by backend middleware)
  if (!localStorage.getItem("tenantId")) {
    localStorage.setItem("tenantId", "default");
  }

  if (!role) {
    return <AuthGateway onSignedIn={() => setAuthVersion((v) => v + 1)} />;
  }

  void authVersion;

  return (
    <WizardProvider>
      <AppShell 
        onNavigate={(page: any) => {
          if (page === 'Dashboard') setCurrentPage('dashboard');
          if (page === 'Releases') setCurrentPage('dashboard');
          if (page === 'Sandbox') setCurrentPage('sandbox');
          if (page === 'Reporting') setCurrentPage('analytics');
          if (page === 'Validation') setCurrentPage('validation');
          if (page === 'Settings') setCurrentPage('automation');
        }}
        userRole={role}
        userId={userId}
        onLogout={() => {
          clearAuthSession();
          setCurrentPage('dashboard');
          setActiveReleaseId(null);
          setAuthVersion((v) => v + 1);
        }}
        activePage={
          currentPage === 'dashboard'
            ? 'Dashboard'
            : currentPage === 'releaseDetail'
              ? 'Releases'
              : currentPage === 'sandbox'
                ? 'Sandbox'
                : currentPage === 'analytics'
                  ? 'Reporting'
                  : currentPage === 'validation'
                    ? 'Validation'
                  : currentPage === 'automation'
                    ? 'Settings'
                : 'Wizard'
        }
      >
        {currentPage === 'wizard' ? (
          <ReleaseWizard onFinish={() => setCurrentPage('dashboard')} />
        ) : currentPage === 'releaseDetail' && activeReleaseId ? (
          <ReleaseDetail
            releaseId={activeReleaseId}
            onBack={() => setCurrentPage('dashboard')}
          />
        ) : currentPage === 'sandbox' ? (
          role === 'admin' ? <SandboxMonitor /> : <Dashboard onNewRelease={() => setCurrentPage('wizard')} onOpenRelease={(id) => { setActiveReleaseId(id); setCurrentPage('releaseDetail'); }} />
        ) : currentPage === 'analytics' ? (
          role === 'admin' ? <AnalyticsDashboard /> : <Dashboard onNewRelease={() => setCurrentPage('wizard')} onOpenRelease={(id) => { setActiveReleaseId(id); setCurrentPage('releaseDetail'); }} />
        ) : currentPage === 'validation' ? (
          role === 'admin' ? (
            <ValidationCenter
              onOpenRelease={(id) => {
                setActiveReleaseId(id);
                setCurrentPage('releaseDetail');
              }}
            />
          ) : (
            <Dashboard onNewRelease={() => setCurrentPage('wizard')} onOpenRelease={(id) => { setActiveReleaseId(id); setCurrentPage('releaseDetail'); }} />
          )
        ) : currentPage === 'automation' ? (
          role === 'admin' ? <AutomationCenter /> : <Dashboard onNewRelease={() => setCurrentPage('wizard')} onOpenRelease={(id) => { setActiveReleaseId(id); setCurrentPage('releaseDetail'); }} />
        ) : (
          <Dashboard
            onNewRelease={() => setCurrentPage('wizard')}
            onOpenRelease={(id) => {
              setActiveReleaseId(id);
              setCurrentPage('releaseDetail');
            }}
          />
        )}
      </AppShell>
    </WizardProvider>
  );
}

export default App;
