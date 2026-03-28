// auth.ts — JWT-aware auth store for AP Studios
import { create } from "zustand";
import { persist } from "zustand/middleware";

export interface AuthUser {
  id: string;
  email: string;
  role: "admin" | "artist" | "staff";
  tenant_id: string;
  artist_id?: string;
}

interface AuthState {
  user: AuthUser | null;
  accessToken: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;

  login: (email: string, password: string, tenant_id?: string) => Promise<void>;
  register: (email: string, password: string, tenant_id?: string) => Promise<void>;
  logout: () => Promise<void>;
  refresh: () => Promise<boolean>;
  getHeaders: (includeJsonContentType?: boolean) => Record<string, string>;
}

const API = import.meta.env.VITE_API_URL ?? "/api";

export const useAuth = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      accessToken: null,
      refreshToken: null,
      isAuthenticated: false,

      login: async (email, password, tenant_id = "default") => {
        const res = await fetch(`${API}/auth/login`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-Tenant-Id": tenant_id,
          },
          body: JSON.stringify({ email, password, tenant_id }),
        });
        if (!res.ok) {
          const err = await res.json().catch(() => ({}));
          throw new Error(err.detail ?? "Login failed");
        }
        const data = await res.json();
        set({
          user: data.user,
          accessToken: data.access_token,
          refreshToken: data.refresh_token,
          isAuthenticated: true,
        });
      },

      register: async (email, password, tenant_id = "default") => {
        const res = await fetch(`${API}/auth/register`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-Tenant-Id": tenant_id,
          },
          body: JSON.stringify({
            email,
            password,
            role: "artist",
            tenant_id,
          }),
        });
        if (!res.ok) {
          const err = await res.json().catch(() => ({}));
          throw new Error(err.detail ?? "Registration failed");
        }
        const data = await res.json();
        set({
          user: data.user,
          accessToken: data.access_token,
          refreshToken: data.refresh_token,
          isAuthenticated: true,
        });
      },

      logout: async () => {
        const { accessToken, user } = get();
        if (accessToken) {
          await fetch(`${API}/auth/logout`, {
            method: "POST",
            headers: {
              Authorization: `Bearer ${accessToken}`,
              "X-Tenant-Id": user?.tenant_id ?? "default",
            },
          }).catch(() => {});
        }
        set({
          user: null,
          accessToken: null,
          refreshToken: null,
          isAuthenticated: false,
        });
      },

      refresh: async () => {
        const { refreshToken, user } = get();
        if (!refreshToken) return false;
        try {
          const res = await fetch(`${API}/auth/refresh`, {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              "X-Tenant-Id": user?.tenant_id ?? "default",
            },
            body: JSON.stringify({ refresh_token: refreshToken }),
          });
          if (!res.ok) {
            set({ user: null, accessToken: null, refreshToken: null, isAuthenticated: false });
            return false;
          }
          const data = await res.json();
          set({ accessToken: data.access_token });
          return true;
        } catch {
          return false;
        }
      },

      getHeaders: (includeJsonContentType = true) => {
        const { accessToken, user } = get();
        const headers: Record<string, string> = {
          "X-Tenant-Id": user?.tenant_id ?? "default",
        };
        if (includeJsonContentType) {
          headers["Content-Type"] = "application/json";
        }
        if (accessToken) {
          headers["Authorization"] = `Bearer ${accessToken}`;
        }
        return headers;
      },
    }),
    {
      name: "ap-studios-auth",
      partialize: (state) => ({
        user: state.user,
        accessToken: state.accessToken,
        refreshToken: state.refreshToken,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
);

// Legacy type export — keeps AppShell.tsx import working
export type UserRole = AuthUser["role"];

// Legacy helpers — kept for any remaining tests/components that use them
export const getUserRole = (): string | null => {
  const state = useAuth.getState();
  return state.user?.role ?? null;
};
export const getUserId = (): string | null => {
  const state = useAuth.getState();
  return state.user?.id ?? null;
};
export const clearAuthSession = (): void => {
  useAuth.getState().logout();
};
// AuthGateway compat shim (legacy pre-JWT gate — no longer used in routing)
export const setAuthSession = (_role: UserRole, _userId: string): void => {
  // no-op: JWT login is now handled by LoginPage / useAuth.login()
  console.warn("setAuthSession is deprecated — use useAuth.login() instead");
};

// Interceptor global para refrescar token en 401
export async function fetchWithAuth(
  url: string,
  options: RequestInit = {}
): Promise<Response> {
  const { getHeaders, refresh, logout } = useAuth.getState();
  const res = await fetch(url, {
    ...options,
    headers: { ...getHeaders(!(options.body instanceof FormData)), ...(options.headers ?? {}) },
  });
  if (res.status === 401) {
    const refreshed = await refresh();
    if (refreshed) {
      return fetch(url, {
        ...options,
        headers: { ...getHeaders(!(options.body instanceof FormData)), ...(options.headers ?? {}) },
      });
    }
    await logout();
  }
  return res;
}
