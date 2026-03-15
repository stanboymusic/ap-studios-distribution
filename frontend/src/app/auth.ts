export type UserRole = "artist" | "admin";

const AUTH_ROLE_KEY = "userRole";
const AUTH_USER_KEY = "userId";

export function getUserRole(): UserRole | null {
  const role = (localStorage.getItem(AUTH_ROLE_KEY) || "").trim().toLowerCase();
  if (role === "artist" || role === "admin") return role;
  return null;
}

export function getUserId(): string | null {
  const userId = (localStorage.getItem(AUTH_USER_KEY) || "").trim();
  return userId || null;
}

export function isAdminRole(): boolean {
  return getUserRole() === "admin";
}

export function setAuthSession(role: UserRole, userId: string) {
  localStorage.setItem(AUTH_ROLE_KEY, role);
  localStorage.setItem(AUTH_USER_KEY, userId.trim());
}

export function clearAuthSession() {
  localStorage.removeItem(AUTH_ROLE_KEY);
  localStorage.removeItem(AUTH_USER_KEY);
}

