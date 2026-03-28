import { useState } from "react";
import { useNavigate, useLocation, Link } from "react-router-dom";
import { useAuth } from "../app/auth";

export default function LoginPage() {
  const { login, user } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [tenant, setTenant] = useState("default");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  if (user) {
    navigate(user.role === "admin" ? "/admin" : "/artist", { replace: true });
  }

  const from = (location.state as any)?.from?.pathname;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await login(email, password, tenant);
      // Read user from getState() — React hook hasn't re-rendered yet
      const { user: freshUser } = useAuth.getState();
      const dest = from ?? (freshUser?.role === "admin" ? "/admin" : "/artist");
      navigate(dest, { replace: true });
    } catch (err: any) {
      setError(err.message ?? "Login failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center px-4">
      <div className="w-full max-w-[440px] fade-up">
        <div className="mb-8 text-center">
          <h1 className="page-title" style={{ fontSize: 28 }}>
            AP Studios
          </h1>
          <p className="page-subtitle" style={{ fontSize: 15 }}>
            Music Distribution Platform
          </p>
        </div>

        <div className="card p-8" style={{ borderRadius: 16 }}>
          <h2 style={{ fontSize: 22, color: "#fff", marginBottom: 18 }}>
            Sign in
          </h2>

          {error && (
            <div
              style={{
                marginBottom: 16,
                padding: "8px 10px",
                background: "rgba(168,56,90,0.12)",
                border: "0.5px solid rgba(168,56,90,0.35)",
                borderRadius: 8,
                color: "#E8C98A",
                fontSize: 14,
              }}
            >
              {error}
            </div>
          )}

          <form className="space-y-4" onSubmit={handleSubmit}>
            <div>
              <label>Email</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@example.com"
                autoComplete="email"
              />
            </div>

            <div>
              <label>Password</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="********"
                autoComplete="current-password"
              />
            </div>

            <div>
              <label>
                Label / Tenant <span style={{ opacity: 0.6 }}>(optional)</span>
              </label>
              <input
                type="text"
                value={tenant}
                onChange={(e) => setTenant(e.target.value)}
                placeholder="default"
              />
            </div>

            <button
              type="submit"
              disabled={loading || !email || !password}
              className="btn-primary w-full justify-center"
              style={{ padding: "12px 20px" }}
            >
              {loading ? "Signing in..." : "Sign in"}
            </button>
          </form>

          <p className="text-center mt-5" style={{ color: "var(--mist-d)", fontSize: 12 }}>
            Don't have an account?{" "}
            <Link
              to="/register"
              style={{ color: "var(--gold)", textDecoration: "none", fontSize: 14 }}
            >
              Create artist account
            </Link>
          </p>
        </div>

        <p className="text-center mt-4" style={{ color: "var(--mist-d)", fontSize: 12 }}>
          AP Studios Distribution - DPID PA-DPIDA-202402050E-4
        </p>
      </div>
    </div>
  );
}
