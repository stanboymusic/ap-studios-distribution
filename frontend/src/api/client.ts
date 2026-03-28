import { fetchWithAuth, useAuth } from "../app/auth";

export const API_BASE = import.meta.env.VITE_API_URL ?? "/api";

export function getApiHeaders(
  extra?: HeadersInit,
  includeJsonContentType: boolean = true
): HeadersInit {
  const { getHeaders } = useAuth.getState();
  const base = getHeaders(includeJsonContentType);
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
  const res = await fetchWithAuth(`${API_BASE}${path}`, {
    headers: getApiHeaders(options?.headers, !hasFormDataBody),
    ...options,
  });

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: "Unknown error" }));
    throw new Error(error.detail ?? "API Error");
  }

  return res.json();
}
