export type Tenant = {
  id: string;
  name: string;
  slug?: string;
  settings?: {
    branding?: {
      primaryColor?: string;
      logoText?: string;
    };
    demo_mode?: boolean;
  };
  created_at?: string;
};

export const TENANT_STORAGE_KEY = "tenantId";

export function getTenantId() {
  return localStorage.getItem(TENANT_STORAGE_KEY) || "default";
}

export function setTenantId(id: string) {
  localStorage.setItem(TENANT_STORAGE_KEY, id);
}

export function applyTenantBranding(tenant: Tenant | null) {
  const root = document.documentElement;
  const primary = tenant?.settings?.branding?.primaryColor || "#1B4079";
  root.style.setProperty("--brand-primary", primary);
  root.style.setProperty("--brand-tenant-name", tenant?.name || "AP Studios");
}

