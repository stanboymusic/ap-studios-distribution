import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { apiFetch } from "../../api/client";

interface UserDetail {
  id: string;
  email: string;
  role: string;
  is_active: boolean;
  release_count: number;
  created_at: string;
  tenant_id: string;
  artist_id?: string;
}

interface ReleaseRow {
  id: string;
  title: string;
  status: string;
  release_type: string;
  upc?: string;
}

export default function UserDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [user, setUser] = useState<UserDetail | null>(null);
  const [releases, setReleases] = useState<ReleaseRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    setLoading(true);
    setError(null);
    Promise.all([
      apiFetch<UserDetail>(`/admin/users/${id}`),
      apiFetch<{ releases: ReleaseRow[] }>(`/admin/users/${id}/releases`),
    ])
      .then(([userData, releasesData]) => {
        setUser(userData);
        setReleases(releasesData.releases ?? []);
      })
      .catch((e: any) => setError(e.message))
      .finally(() => setLoading(false));
  }, [id]);

  const handleToggleActive = async () => {
    if (!user) return;
    setActionLoading(true);
    setSuccess(null);
    setError(null);
    try {
      const updated = await apiFetch<UserDetail>(`/admin/users/${user.id}`, {
        method: "PATCH",
        body: JSON.stringify({ is_active: !user.is_active }),
      });
      setUser(updated);
      setSuccess(
        updated.is_active ? "Account enabled successfully." : "Account disabled."
      );
    } catch (e: any) {
      setError(e.message);
    } finally {
      setActionLoading(false);
    }
  };

  const statusPill: Record<string, string> = {
    CREATED: "pill-gold",
    VALIDATED: "pill-blue",
    DELIVERED: "pill-green",
    FAILED: "pill-wine",
  };

  if (loading) {
    return (
      <div className="p-6 text-gray-400 text-sm">Loading user...</div>
    );
  }

  if (!user) {
    return (
      <div className="p-6">
        <p className="text-red-400 text-sm">{error ?? "User not found"}</p>
        <Link to="/admin/users" className="text-indigo-400 text-sm mt-2 block">
          &lt;- Back to users
        </Link>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-4xl mx-auto">
      {/* Back */}
      <Link
        to="/admin/users"
        className="text-gray-500 hover:text-gray-400 transition-colors mb-6 block"
        style={{ fontSize: 15 }}
      >
        &lt;- Back to users
      </Link>

      {/* Alerts */}
      {error && (
        <div className="mb-4 px-3 py-2 bg-red-500/10 border border-red-500/30
                        rounded-md text-red-400 text-sm">
          {error}
        </div>
      )}
      {success && (
        <div className="mb-4 px-3 py-2 bg-green-500/10 border border-green-500/30
                        rounded-md text-green-400 text-sm">
          {success}
        </div>
      )}

      {/* User card */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-5 mb-6">
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-2xl font-bold text-white">{user.email}</h1>
            <p className="text-gray-500 font-mono mt-1" style={{ fontSize: 13 }}>
              {user.id}
            </p>
          </div>

          {/* Toggle active button - hidden for admin accounts */}
          {user.role !== "admin" && (
            <button
              onClick={handleToggleActive}
              disabled={actionLoading}
              className={`font-medium px-4 py-2 rounded-md transition-colors
                          disabled:opacity-50 ${
                user.is_active
                  ? "bg-red-500/10 text-red-400 hover:bg-red-500/20 border border-red-500/30"
                  : "bg-green-500/10 text-green-400 hover:bg-green-500/20 border border-green-500/30"
              }`}
              style={{ fontSize: 15 }}
            >
              {actionLoading
                ? "..."
                : user.is_active
                ? "Disable account"
                : "Enable account"}
            </button>
          )}
        </div>

        {/* Metadata grid */}
        <div className="grid grid-cols-2 gap-4 mt-5 sm:grid-cols-4">
          {[
            { label: "Role", value: user.role },
            { label: "Status", value: user.is_active ? "Active" : "Disabled" },
            { label: "Tenant", value: user.tenant_id },
            { label: "Releases", value: String(releases.length) },
          ].map(({ label, value }) => (
            <div key={label}>
              <p
                className="text-gray-500 uppercase tracking-wide mb-1"
                style={{ fontSize: 13 }}
              >
                {label}
              </p>
              <p className="text-white" style={{ fontSize: 15 }}>
                {value}
              </p>
            </div>
          ))}
        </div>

        {user.artist_id && (
          <div className="mt-4 pt-4 border-t border-gray-800">
            <p
              className="text-gray-500 uppercase tracking-wide mb-1"
              style={{ fontSize: 13 }}
            >
              Linked Artist ID
            </p>
            <p className="text-gray-400 font-mono" style={{ fontSize: 13 }}>
              {user.artist_id}
            </p>
          </div>
        )}
      </div>

      {/* Releases table */}
      <div>
        <h2
          className="font-semibold text-gray-300 mb-3 uppercase tracking-wide"
          style={{ fontSize: 16 }}
        >
          Releases ({releases.length})
        </h2>

        {releases.length === 0 ? (
          <p className="text-gray-500 text-sm">No releases yet.</p>
        ) : (
          <div className="bg-gray-900 border border-gray-800 rounded-xl 
                          overflow-hidden">
            <div className="grid grid-cols-12 gap-4 px-4 py-3 border-b
                            border-gray-800 text-gray-500 uppercase
                            tracking-wide" style={{ fontSize: 13 }}>
              <div className="col-span-5">Title</div>
              <div className="col-span-2">Type</div>
              <div className="col-span-3">UPC</div>
              <div className="col-span-2">Status</div>
            </div>

            {releases.map((r) => (
              <div
                key={r.id}
                className="grid grid-cols-12 gap-4 px-4 py-3 border-b
                           border-gray-800/50 last:border-0 items-center
                           hover:bg-gray-800/30 transition-colors"
              >
                <div className="col-span-5">
                  <Link
                    to={`/admin/releases/${r.id}`}
                    className="text-white hover:text-indigo-300 transition-colors truncate block"
                    style={{ fontSize: 15 }}
                  >
                    {r.title}
                  </Link>
                </div>
                <div className="col-span-2 text-gray-400" style={{ fontSize: 13 }}>
                  {r.release_type}
                </div>
                <div className="col-span-3 text-gray-500 font-mono" style={{ fontSize: 13 }}>
                  {r.upc ?? "-"}
                </div>
                <div className="col-span-2">
                  <span className={`pill ${statusPill[r.status] ?? statusPill.CREATED}`}>
                    {r.status}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
