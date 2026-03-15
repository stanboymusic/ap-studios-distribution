export const API_BASE = "http://127.0.0.1:8000/api";
import { getUserId, getUserRole } from "../app/auth";

export function getApiHeaders(extra?: HeadersInit, includeJsonContentType: boolean = true): HeadersInit {
  const tenantId = localStorage.getItem("tenantId") || "default";
  const role = getUserRole() || "artist";
  const userId = getUserId() || `${role}:anonymous`;
  const base: HeadersInit = {
    "X-Tenant-Id": tenantId,
    "X-User-Role": role,
    "X-User-Id": userId,
  };
  if (includeJsonContentType) {
    (base as Record<string, string>)["Content-Type"] = "application/json";
  }
  return {
    ...base,
    ...(extra || {}),
  };
}

export async function apiFetch<T>(
  path: string,
  options?: RequestInit
): Promise<T> {
  const hasFormDataBody = typeof FormData !== "undefined" && options?.body instanceof FormData;
  const res = await fetch(`${API_BASE}${path}`, {
    headers: getApiHeaders(options?.headers, !hasFormDataBody),
    ...options,
  });

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: "Unknown error" }));
    throw new Error(error.detail ?? "API Error");
  }

  return res.json();
}
