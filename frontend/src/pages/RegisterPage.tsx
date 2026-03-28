import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { useAuth } from "../app/auth";

export default function RegisterPage() {
  const { register, user, isAuthenticated } = useAuth();
  const navigate = useNavigate();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [tenant, setTenant] = useState("default");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  // Si ya está autenticado, redirigir
  if (isAuthenticated && user) {
    navigate(user.role === "admin" ? "/admin" : "/artist", { replace: true });
  }

  const validateForm = (): string | null => {
    if (!email.trim()) return "Email is required";
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) return "Invalid email format";
    if (password.length < 8) return "Password must be at least 8 characters";
    if (password !== confirmPassword) return "Passwords do not match";
    return null;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const validationError = validateForm();
    if (validationError) {
      setError(validationError);
      return;
    }
    setError(null);
    setLoading(true);
    try {
      await register(email.trim().toLowerCase(), password, tenant);
      navigate("/artist", { replace: true });
    } catch (err: any) {
      setError(err.message ?? "Registration failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center px-4">
      <div className="w-full max-w-[440px] fade-up">
        {/* Header */}
        <div className="mb-8 text-center">
          <h1 className="page-title" style={{ fontSize: 28 }}>
            AP Studios
          </h1>
          <p className="page-subtitle" style={{ fontSize: 15 }}>
            Music Distribution Platform
          </p>
        </div>

        {/* Card */}
        <div className="card p-8" style={{ borderRadius: 16 }}>
          <h2 style={{ fontSize: 22, color: "#fff", marginBottom: 4 }}>
            Create artist account
          </h2>
          <p style={{ fontSize: 14, color: "var(--mist-d)", marginBottom: 18 }}>
            Start distributing your music worldwide
          </p>

          {/* Error */}
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

          <div className="space-y-4">
            {/* Email */}
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

            {/* Password */}
            <div>
              <label>Password</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Min. 8 characters"
                autoComplete="new-password"
              />
            </div>

            {/* Confirm Password */}
            <div>
              <label>Confirm password</label>
              <input
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder="********"
                autoComplete="new-password"
              />
            </div>

            {/* Tenant (label / company) - optional */}
            <details className="group">
              <summary className="text-sm cursor-pointer transition-colors list-none flex items-center gap-1" style={{ color: "var(--mist-d)" }}>
                <span className="group-open:rotate-90 transition-transform inline-block">{">"}</span>
                Advanced - Label / Tenant ID
              </summary>
              <div className="mt-2">
                <input
                  type="text"
                  value={tenant}
                  onChange={(e) => setTenant(e.target.value)}
                  placeholder="default"
                />
                <p style={{ fontSize: 14, color: "var(--mist-d)", marginTop: 6 }}>
                  Leave as "default" unless your label has a custom tenant.
                </p>
              </div>
            </details>

            {/* Password strength hint */}
            {password.length > 0 && password.length < 8 && (
              <p style={{ fontSize: 14, color: "var(--gold)" }}>
                Password too short ({password.length}/8 characters)
              </p>
            )}

            {/* Submit */}
            <button
              onClick={handleSubmit}
              disabled={loading || !email || !password || !confirmPassword}
              className="btn-primary w-full justify-center"
              style={{ padding: "12px 20px" }}
            >
              {loading ? "Creating account..." : "Create account"}
            </button>
          </div>

          {/* Login link */}
          <p className="text-center mt-5" style={{ color: "var(--mist-d)", fontSize: 12 }}>
            Already have an account?{" "}
            <Link
              to="/login"
              style={{ color: "var(--gold)", textDecoration: "none", fontSize: 14 }}
            >
              Sign in
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
