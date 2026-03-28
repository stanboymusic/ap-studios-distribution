import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../../app/auth";
import { apiFetch } from "../../api/client";

interface Release {
  id: string;
  title: string;
  status: string;
  release_type: string;
  upc?: string;
  created_at?: string;
  owner_user_id?: string;
}

export default function ArtistDashboard() {
  const { user } = useAuth();
  const [releases, setReleases] = useState<Release[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    apiFetch("/releases")
      .then((r) => (r as any))
      .then((data) => {
        const list = Array.isArray(data) ? data : data.releases ?? [];
        const mine = list.filter(
          (r: Release) => !r.owner_user_id || r.owner_user_id === user?.id
        );
        setReleases(mine);
      })
      .catch((e: any) => setError(e.message))
      .finally(() => setLoading(false));
  }, [user?.id]);

  const statusPill: Record<string, string> = {
    CREATED: "pill-gold",
    VALIDATED: "pill-blue",
    DELIVERED: "pill-green",
    FAILED: "pill-wine",
  };

  return (
    <div className="p-6 max-w-5xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-white">My Releases</h1>
          <p className="text-gray-400 mt-0.5" style={{ fontSize: 15 }}>
            {user?.email}
          </p>
        </div>
        <Link
          to="/artist/new"
          className="btn-primary"
          style={{ textDecoration: "none" }}
        >
          + New Release
        </Link>
      </div>

      {loading && <p className="text-gray-400 text-sm">Loading releases...</p>}

      {error && <p className="text-red-400 text-sm">Error: {error}</p>}

      {!loading && !error && releases.length === 0 && (
        <div className="text-center py-16 text-gray-500">
          <p className="text-[20px]">No releases yet</p>
          <p className="text-base mt-1">Start by creating your first release.</p>
          <Link
            to="/artist/new"
            className="inline-block mt-4 text-indigo-400 hover:text-indigo-300 text-sm transition-colors"
            style={{ fontSize: 14 }}
          >
            Create release →
          </Link>
        </div>
      )}

      <div className="space-y-2">
        {releases.map((release) => (
          <div
            key={release.id}
            className="bg-gray-900 border border-gray-800 rounded-lg px-4 py-[18px] flex items-center justify-between hover:border-gray-700 transition-colors"
          >
            <div>
              <p className="text-white font-medium text-base">{release.title}</p>
              <p className="text-gray-500 mt-0.5" style={{ fontSize: 13 }}>
                {release.release_type}
                {release.upc ? ` · UPC ${release.upc}` : ""}
              </p>
            </div>
            <div className="flex items-center gap-3">
              <span
                className={`pill ${statusPill[release.status] ?? statusPill.CREATED}`}
              >
                {release.status}
              </span>
              <Link
                to={`/artist/releases/${release.id}`}
                className="text-indigo-400 hover:text-indigo-300 transition-colors"
                style={{ fontSize: 14 }}
              >
                View →
              </Link>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
