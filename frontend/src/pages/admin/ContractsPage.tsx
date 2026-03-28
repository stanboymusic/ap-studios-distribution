import { useEffect, useState } from "react";
import { apiFetch } from "../../api/client";

interface ContractRow {
  id: string;
  user_id: string;
  email: string;
  version: string;
  accepted_at: string;
  ip_address: string | null;
  is_current_version: boolean;
}

export default function ContractsPage() {
  const [contracts, setContracts] = useState<ContractRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [currentVersion, setCurrentVersion] = useState("");

  useEffect(() => {
    apiFetch<{ contracts: ContractRow[]; current_version: string }>("/admin/contracts")
      .then((data) => {
        setContracts(data.contracts ?? []);
        setCurrentVersion(data.current_version ?? "");
      })
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="p-6 max-w-6xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-white">Contracts</h1>
          <p className="text-gray-400 mt-0.5" style={{ fontSize: 15 }}>
            {contracts.length} signed · Current version: v{currentVersion}
          </p>
        </div>
      </div>

      {loading && <p className="text-gray-400 text-sm">Loading...</p>}

      {!loading && (
        <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
          <div
            className="grid grid-cols-12 gap-4 px-4 py-4 border-b border-gray-800 text-gray-500 uppercase tracking-wide"
            style={{ fontSize: 13 }}
          >
            <div className="col-span-4">Artist</div>
            <div className="col-span-2">Version</div>
            <div className="col-span-3">Accepted at</div>
            <div className="col-span-2">IP</div>
            <div className="col-span-1">Status</div>
          </div>

          {contracts.length === 0 && (
            <div className="px-4 py-10 text-center text-gray-500 text-sm">
              No contracts signed yet.
            </div>
          )}

          {contracts.map((c) => (
            <div
              key={c.id}
              className="grid grid-cols-12 gap-4 px-4 py-4 border-b border-gray-800/50 last:border-0 items-center hover:bg-gray-800/30 transition-colors"
            >
              <div className="col-span-4">
                <p className="text-white truncate" style={{ fontSize: 15 }}>
                  {c.email}
                </p>
                <p className="text-gray-600 font-mono truncate" style={{ fontSize: 13 }}>
                  {c.user_id}
                </p>
              </div>
              <div className="col-span-2 text-gray-400" style={{ fontSize: 13 }}>
                v{c.version}
              </div>
              <div className="col-span-3 text-gray-400" style={{ fontSize: 13 }}>
                {new Date(c.accepted_at).toLocaleString()}
              </div>
              <div className="col-span-2 text-gray-500 font-mono" style={{ fontSize: 13 }}>
                {c.ip_address ?? "—"}
              </div>
              <div className="col-span-1">
                <span
                  className={`pill ${
                    c.is_current_version ? "pill-green" : "pill-gold"
                  }`}
                >
                  {c.is_current_version ? "✓" : "old"}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
