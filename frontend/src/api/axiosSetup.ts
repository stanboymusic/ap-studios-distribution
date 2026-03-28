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
