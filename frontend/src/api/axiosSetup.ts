import axios from "axios";
import { getUserId, getUserRole } from "../app/auth";

// Ensure every axios request to the backend includes tenant context.
axios.interceptors.request.use((config) => {
  const tenantId = localStorage.getItem("tenantId") || "default";
  const role = getUserRole() || "artist";
  const userId = getUserId() || `${role}:anonymous`;
  config.headers = config.headers || {};
  if (!("X-Tenant-Id" in config.headers)) {
    (config.headers as any)["X-Tenant-Id"] = tenantId;
  }
  if (!("X-User-Role" in config.headers)) {
    (config.headers as any)["X-User-Role"] = role;
  }
  if (!("X-User-Id" in config.headers)) {
    (config.headers as any)["X-User-Id"] = userId;
  }
  return config;
});
