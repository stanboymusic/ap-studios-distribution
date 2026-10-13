import axios from "axios";
import { useAuth } from "../app/auth";

// Ensure every axios request to the backend includes tenant context.
axios.interceptors.request.use((config) => {
  const { accessToken, user } = useAuth.getState();
  const tenantId = user?.tenant_id || "default";
  config.headers = config.headers || {};
  if (!("X-Tenant-Id" in config.headers)) {
    (config.headers as any)["X-Tenant-Id"] = tenantId;
  }
  if (accessToken && !("Authorization" in config.headers)) {
    (config.headers as any)["Authorization"] = `Bearer ${accessToken}`;
  }
  return config;
});

// ── Renovación automática de sesión ──────────────────────────────
// El token de acceso dura 60 min. Si la API responde 401, se intenta renovar con el
// refresh token UNA vez y se repite la petición; si no se puede, useAuth.refresh() cierra la sesión.
let refreshing: Promise<boolean> | null = null;
const renewSession = () => {
  if (!refreshing) {
    refreshing = useAuth.getState().refresh().finally(() => {
      refreshing = null;
    });
  }
  return refreshing;
};
const isAuthRoute = (url: string) => url.includes("/auth/");

// axios
axios.interceptors.response.use(undefined, async (error) => {
  const cfg = error?.config;
  if (error?.response?.status === 401 && cfg && !cfg.__retried && !isAuthRoute(cfg.url || "")) {
    cfg.__retried = true;
    if (await renewSession()) {
      cfg.headers = { ...(cfg.headers || {}), Authorization: `Bearer ${useAuth.getState().accessToken}` };
      return axios(cfg);
    }
  }
  return Promise.reject(error);
});

// fetch (los pasos del wizard usan fetch directo)
const nativeFetch = window.fetch.bind(window);
window.fetch = async (input: RequestInfo | URL, init?: RequestInit) => {
  const res = await nativeFetch(input, init);
  const url = typeof input === "string" ? input : input instanceof URL ? input.href : input.url;
  if (res.status !== 401 || !url.includes("/api/") || isAuthRoute(url)) return res;
  if (!(await renewSession())) return res;
  const headers = new Headers(init?.headers ?? (input instanceof Request ? input.headers : undefined));
  headers.set("Authorization", `Bearer ${useAuth.getState().accessToken}`);
  return nativeFetch(input, { ...init, headers });
};
