import React, { useEffect, useMemo, useState } from 'react';
import { apiFetch } from '../../api/client';
import { applyTenantBranding, getTenantId, setTenantId, type Tenant } from '../../app/tenant';
import { type UserRole } from '../../app/auth';

interface AppShellProps {
  children: React.ReactNode;
  onNavigate?: (page: string) => void;
  activePage?: string;
  userRole?: UserRole;
  userId?: string;
  onLogout?: () => void;
}

export default function AppShell({
  children,
  onNavigate,
  activePage = "Dashboard",
  userRole = "artist",
  userId,
  onLogout,
}: AppShellProps) {
  const [tenants, setTenants] = useState<Tenant[]>([]);
  const [activeTenant, setActiveTenant] = useState<Tenant | null>(null);
  const [tenantId, setTenantIdState] = useState<string>(getTenantId());

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const list = await apiFetch<Tenant[]>('/tenants/');
        if (cancelled) return;
        setTenants(list);
      } catch {
        // ignore
      }
      try {
        const t = await apiFetch<Tenant>(`/tenants/${tenantId}`);
        if (cancelled) return;
        setActiveTenant(t);
        applyTenantBranding(t);
      } catch {
        if (cancelled) return;
        setActiveTenant({ id: tenantId, name: tenantId } as Tenant);
        applyTenantBranding({ id: tenantId, name: tenantId } as Tenant);
      }
    }
    load();
    return () => {
      cancelled = true;
    };
  }, [tenantId]);

  const logoText = useMemo(() => {
    return activeTenant?.settings?.branding?.logoText || activeTenant?.name || 'AP Studios';
  }, [activeTenant]);

  const primaryColor = useMemo(() => {
    return activeTenant?.settings?.branding?.primaryColor || '#1B4079';
  }, [activeTenant]);

  return (
    <div className="flex min-h-screen" style={{ background: "var(--ink)", color: "var(--mist)" }}>
      {/* Sidebar */}
      <aside
        className="w-64 flex flex-col"
        style={{ background: "var(--card)", borderRight: "0.5px solid var(--border)" }}
      >
        <div className="p-6">
          <h1 className="text-xl font-bold" style={{ color: primaryColor }}>{logoText}</h1>
          <p
            className="text-sm uppercase tracking-widest font-bold mt-1"
            style={{ color: "var(--mist-d)" }}
          >
            Distribution
          </p>
        </div>
        
        <nav className="flex-1 px-4 space-y-2 mt-4">
          <NavItem 
            active={activePage === "Dashboard"} 
            label="Dashboard" 
            onClick={() => onNavigate?.("Dashboard")}
          />
          <NavItem 
            active={activePage === "Releases"} 
            label="Releases" 
            onClick={() => onNavigate?.("Releases")}
          />
          {userRole === "admin" ? (
            <>
              <NavItem 
                active={activePage === "Validation"} 
                label="Validation" 
                onClick={() => onNavigate?.("Validation")}
              />
              <NavItem 
                active={activePage === "Sandbox"} 
                label="Sandbox" 
                onClick={() => onNavigate?.("Sandbox")}
              />
              <NavItem 
                active={activePage === "Reporting"} 
                label="Reporting" 
                onClick={() => onNavigate?.("Reporting")}
              />
              <NavItem 
                active={activePage === "Settings"} 
                label="Settings" 
                onClick={() => onNavigate?.("Settings")}
              />
            </>
          ) : null}
        </nav>
      </aside>

      {/* Main Content */}
      <div className="flex-1 flex flex-col">
        <header
          className="h-16 flex items-center justify-between px-8"
          style={{ background: "var(--card)", borderBottom: "0.5px solid var(--border)" }}
        >
          <div className="flex items-center gap-4">
            <span className="text-sm" style={{ color: "var(--mist-d)" }}>
              Session: <strong>{userId || "anonymous"}</strong> · Role: <strong>{userRole.toUpperCase()}</strong>
            </span>
            <span className="text-sm" style={{ color: "var(--mist-d)" }}>Tenant:</span>
            <select
              value={tenantId}
              onChange={(e) => {
                const next = e.target.value;
                setTenantId(next);
                setTenantIdState(next);
                // reload to reset cached state/pages cleanly
                window.location.reload();
              }}
              className="text-sm rounded-lg px-3 py-2"
              style={{
                background: "rgba(255,255,255,0.03)",
                border: "0.5px solid var(--border)",
                color: "var(--mist)",
              }}
              title="Switch tenant"
            >
              {tenants.length ? tenants.map((t) => (
                <option key={t.id} value={t.id}>{t.name}</option>
              )) : (
                <option value={tenantId}>{tenantId}</option>
              )}
            </select>
          </div>
          <div className="flex items-center gap-4">
            <button className="text-sm hover:underline" style={{ color: "var(--gold)" }} onClick={onLogout}>
              Switch account
            </button>
            <div className="w-8 h-8 rounded-full flex items-center justify-center text-white text-sm font-bold" style={{ backgroundColor: primaryColor }}>
              AS
            </div>
          </div>
        </header>
        
        <main className="flex-1 overflow-auto">
          {children}
        </main>
      </div>
    </div>
  );
}

function NavItem({ label, active = false, onClick }: { label: string, active?: boolean, onClick?: () => void }) {
  return (
    <button 
      onClick={onClick}
      className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-colors ${
        active ? "nav-item-active" : "nav-item"
      }`}
    >
      {label}
    </button>
  );
}
