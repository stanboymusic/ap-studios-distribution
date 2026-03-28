import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { apiFetch } from "../../api/client";

interface UserRow {
  id: string;
  email: string;
  role: string;
  is_active: boolean;
  release_count: number;
  created_at: string;
  tenant_id: string;
}

export default function UsersListPage() {
  const [users, setUsers] = useState<UserRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState("");

  const fetchUsers = () => {
    setLoading(true);
    setError(null);
    apiFetch<{ users: UserRow[] }>("/admin/users")
      .then((data) => setUsers(data.users ?? []))
      .catch((e: any) => setError(e.message))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchUsers();
  }, []);

  const toggleActive = async (user: UserRow) => {
    try {
      await apiFetch(`/admin/users/${user.id}`, {
        method: "PATCH",
        body: JSON.stringify({ is_active: !user.is_active }),
      });
      fetchUsers();
    } catch (e: any) {
      setError(e.message);
    }
  };

  const filtered = users.filter(
    (u) =>
      u.email.toLowerCase().includes(search.toLowerCase()) ||
      u.role.toLowerCase().includes(search.toLowerCase())
  );

  const roleColor: Record<string, string> = {
    admin: "pill-wine",
    artist: "pill-blue",
    staff: "pill-gold",
  };

  return (
    <div className="p-6 max-w-6xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-white">Users</h1>
          <p className="text-gray-400 mt-0.5" style={{ fontSize: 15 }}>
            {users.length} registered account{users.length !== 1 ? "s" : ""}
          </p>
        </div>
        <input
          type="text"
          placeholder="Search by email or role..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="bg-gray-800 border border-gray-700 rounded-md
                     text-white focus:outline-none focus:border-indigo-500
                     transition-colors w-64"
        />
      </div>

      {/* Error */}
      {error && (
        <div className="mb-4 px-3 py-2 bg-red-500/10 border border-red-500/30
                        rounded-md text-red-400 text-sm">
          {error}
        </div>
      )}

      {/* Loading */}
      {loading && (
        <p className="text-gray-400 text-sm">Loading users...</p>
      )}

      {/* Table */}
      {!loading && (
        <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
          {/* Table header */}
          <div className="grid grid-cols-12 gap-4 px-4 py-4 border-b border-gray-800
                          text-gray-500 uppercase tracking-wide" style={{ fontSize: 13 }}>
            <div className="col-span-4">Email</div>
            <div className="col-span-2">Role</div>
            <div className="col-span-2 text-center">Releases</div>
            <div className="col-span-2">Status</div>
            <div className="col-span-2 text-right">Actions</div>
          </div>

          {/* Rows */}
          {filtered.length === 0 && (
            <div className="px-4 py-10 text-center text-gray-500 text-sm">
              {search ? "No users match your search." : "No users registered yet."}
            </div>
          )}

          {filtered.map((user) => (
            <div
              key={user.id}
              className="grid grid-cols-12 gap-4 px-4 py-4 border-b
                         border-gray-800/50 last:border-0 items-center
                         hover:bg-gray-800/30 transition-colors"
            >
              {/* Email */}
              <div className="col-span-4">
                <p className="text-white truncate" style={{ fontSize: 15 }}>
                  {user.email}
                </p>
                <p
                  className="text-gray-600 font-mono mt-0.5 truncate"
                  style={{ fontSize: 12 }}
                >
                  {user.id}
                </p>
              </div>

              {/* Role */}
              <div className="col-span-2">
                <span className={`pill ${roleColor[user.role] ?? roleColor.artist}`}>
                  {user.role}
                </span>
              </div>

              {/* Release count */}
              <div className="col-span-2 text-center">
                <span className="text-white text-sm font-medium">
                  {user.release_count}
                </span>
              </div>

              {/* Status */}
              <div className="col-span-2">
                <span className={`pill ${user.is_active ? "pill-green" : "pill-wine"}`}>
                  {user.is_active ? "Active" : "Disabled"}
                </span>
              </div>

              {/* Actions */}
              <div className="col-span-2 flex items-center justify-end gap-3">
                <Link
                  to={`/admin/users/${user.id}`}
                  className="text-indigo-400 hover:text-indigo-300 transition-colors"
                  style={{ fontSize: 14 }}
                >
                  View
                </Link>
                {user.role !== "admin" && (
                  <button
                    onClick={() => toggleActive(user)}
                    className={`transition-colors ${
                      user.is_active
                        ? "text-red-400 hover:text-red-300"
                        : "text-green-400 hover:text-green-300"
                    }`}
                    style={{ fontSize: 14 }}
                  >
                    {user.is_active ? "Disable" : "Enable"}
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
