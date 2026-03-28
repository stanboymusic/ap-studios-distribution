import { useEffect, useState } from "react";
import { apiFetch } from "../../api/client";

interface Overview {
  ap_studios_revenue_usd: number;
  total_gross_from_dsps_usd: number;
  total_net_owed_to_artists_usd: number;
  total_paid_out_usd: number;
  total_pending_payouts_usd: number;
  available_to_pay_usd: number;
  artists: ArtistRow[];
}

interface ArtistRow {
  user_id: string;
  email: string;
  total_gross: number;
  total_net: number;
  total_streams: number;
}

interface PayoutRow {
  id: string;
  user_id: string;
  email: string;
  amount: number;
  currency: string;
  method: string;
  status: string;
  reference?: string;
  created_at: string;
  paid_at?: string;
}

const fmt = (n: number) =>
  new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
  }).format(n);

export default function RoyaltiesPage() {
  const [overview, setOverview] = useState<Overview | null>(null);
  const [payouts, setPayouts] = useState<PayoutRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState<"overview" | "payouts">("overview");

  // Create payout modal state
  const [showCreate, setShowCreate] = useState(false);
  const [selectedArtist, setSelectedArtist] = useState<ArtistRow | null>(null);
  const [payoutAmount, setPayoutAmount] = useState("");
  const [payoutMethod, setPayoutMethod] = useState("zelle");
  const [payoutNote, setPayoutNote] = useState("");
  const [creating, setCreating] = useState(false);

  // Mark paid modal state
  const [markingPaid, setMarkingPaid] = useState<string | null>(null);
  const [reference, setReference] = useState("");

  const fetchData = () => {
    setLoading(true);
    Promise.all([
      apiFetch<Overview>("/admin/royalties/overview"),
      apiFetch<{ payouts: PayoutRow[] }>("/admin/royalties/payouts"),
    ])
      .then(([ov, pays]) => {
        setOverview(ov);
        setPayouts(pays.payouts ?? []);
      })
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleCreatePayout = async () => {
    if (!selectedArtist || !payoutAmount) return;
    setCreating(true);
    try {
      await apiFetch("/admin/royalties/payouts", {
        method: "POST",
        body: JSON.stringify({
          user_id: selectedArtist.user_id,
          amount: parseFloat(payoutAmount),
          method: payoutMethod,
          note: payoutNote || null,
        }),
      });
      setShowCreate(false);
      setPayoutAmount("");
      setPayoutNote("");
      fetchData();
    } catch (e: any) {
      alert(e.message);
    } finally {
      setCreating(false);
    }
  };

  const handleMarkPaid = async (payoutId: string) => {
    if (!reference.trim()) return;
    try {
      await apiFetch(`/admin/royalties/payouts/${payoutId}/mark-paid`, {
        method: "PATCH",
        body: JSON.stringify({ reference }),
      });
      setMarkingPaid(null);
      setReference("");
      fetchData();
    } catch (e: any) {
      alert(e.message);
    }
  };

  const statusPill: Record<string, string> = {
    pending: "pill-gold",
    paid: "pill-green",
    failed: "pill-wine",
  };

  if (loading) {
    return <div className="p-6 text-gray-400 text-sm">Loading royalties...</div>;
  }

  return (
    <div className="p-6 max-w-6xl mx-auto">
      <h1 className="text-2xl font-bold text-white mb-6">Royalties & Payouts</h1>

      {/* AP Studios revenue highlight */}
      {overview && (
        <div className="grid grid-cols-2 gap-4 mb-6 sm:grid-cols-3">
          {[
            {
              label: "AP Studios Revenue (15%)",
              value: fmt(overview.ap_studios_revenue_usd),
              highlight: true,
            },
            {
              label: "Gross from DSPs",
              value: fmt(overview.total_gross_from_dsps_usd),
            },
            {
              label: "Net Owed to Artists",
              value: fmt(overview.total_net_owed_to_artists_usd),
            },
            {
              label: "Total Paid Out",
              value: fmt(overview.total_paid_out_usd),
            },
            {
              label: "Pending Payouts",
              value: fmt(overview.total_pending_payouts_usd),
            },
            {
              label: "Available to Pay",
              value: fmt(overview.available_to_pay_usd),
            },
          ].map(({ label, value, highlight }) => (
            <div
              key={label}
              className={`rounded-xl border p-4 ${
                highlight
                  ? "bg-green-900/20 border-green-500/30"
                  : "bg-gray-900 border-gray-800"
              }`}
            >
              <p
                className="text-gray-500 uppercase tracking-wide mb-1"
                style={{ fontSize: 13 }}
              >
                {label}
              </p>
              <p
                className={`text-2xl font-bold ${
                  highlight ? "text-green-300" : "text-white"
                }`}
              >
                {value}
              </p>
            </div>
          ))}
        </div>
      )}

      {/* Tabs */}
      <div className="flex gap-1 mb-4 bg-gray-900 rounded-lg p-1 w-fit">
        {(["overview", "payouts"] as const).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`px-4 py-1.5 rounded-md font-medium transition-colors ${
              tab === t
                ? "bg-indigo-600 text-white"
                : "text-gray-400 hover:text-white"
            }`}
            style={{ fontSize: 15 }}
          >
            {t.charAt(0).toUpperCase() + t.slice(1)}
          </button>
        ))}
      </div>

      {/* Artists overview */}
      {tab === "overview" && overview && (
        <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
          <div
            className="grid grid-cols-12 gap-4 px-4 py-4 border-b border-gray-800 text-gray-500 uppercase tracking-wide"
            style={{ fontSize: 13 }}
          >
            <div className="col-span-4">Artist</div>
            <div className="col-span-2 text-right">Streams</div>
            <div className="col-span-2 text-right">Gross</div>
            <div className="col-span-2 text-right">Net (85%)</div>
            <div className="col-span-2 text-right">Action</div>
          </div>

          {overview.artists.length === 0 && (
            <div className="px-4 py-10 text-center text-gray-500 text-sm">
              No royalty data yet. Process a DSR to see earnings.
            </div>
          )}

          {overview.artists.map((a) => (
            <div
              key={a.user_id}
              className="grid grid-cols-12 gap-4 px-4 py-4 border-b border-gray-800/50 last:border-0 items-center hover:bg-gray-800/30 transition-colors"
            >
              <div className="col-span-4">
                <p className="text-white truncate" style={{ fontSize: 15 }}>
                  {a.email}
                </p>
              </div>
              <div className="col-span-2 text-right text-gray-400" style={{ fontSize: 15 }}>
                {a.total_streams.toLocaleString()}
              </div>
              <div className="col-span-2 text-right text-gray-400" style={{ fontSize: 15 }}>
                {fmt(a.total_gross)}
              </div>
              <div className="col-span-2 text-right text-indigo-300 font-medium" style={{ fontSize: 15 }}>
                {fmt(a.total_net)}
              </div>
              <div className="col-span-2 text-right">
                <button
                  onClick={() => {
                    setSelectedArtist(a);
                    setShowCreate(true);
                  }}
                  className="text-green-400 hover:text-green-300 transition-colors"
                  style={{ fontSize: 14 }}
                >
                  Pay out
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Payouts tab */}
      {tab === "payouts" && (
        <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
          <div
            className="grid grid-cols-12 gap-4 px-4 py-4 border-b border-gray-800 text-gray-500 uppercase tracking-wide"
            style={{ fontSize: 13 }}
          >
            <div className="col-span-3">Artist</div>
            <div className="col-span-2">Amount</div>
            <div className="col-span-2">Method</div>
            <div className="col-span-2">Date</div>
            <div className="col-span-2">Status</div>
            <div className="col-span-1"></div>
          </div>

          {payouts.length === 0 && (
            <div className="px-4 py-10 text-center text-gray-500 text-sm">
              No payouts yet.
            </div>
          )}

          {payouts.map((p) => (
            <div
              key={p.id}
              className="grid grid-cols-12 gap-4 px-4 py-4 border-b border-gray-800/50 last:border-0 items-center"
            >
              <div className="col-span-3 text-white truncate" style={{ fontSize: 15 }}>
                {p.email}
              </div>
              <div className="col-span-2 text-white font-medium" style={{ fontSize: 15 }}>
                {fmt(p.amount)}
              </div>
              <div className="col-span-2 text-gray-400 uppercase" style={{ fontSize: 13 }}>
                {p.method}
              </div>
              <div className="col-span-2 text-gray-400" style={{ fontSize: 13 }}>
                {new Date(p.created_at).toLocaleDateString()}
              </div>
              <div className="col-span-2">
                <span
                  className={`pill ${statusPill[p.status] ?? statusPill.pending}`}
                >
                  {p.status}
                </span>
              </div>
              <div className="col-span-1 text-right">
                {p.status === "pending" && (
                  <button
                    onClick={() => setMarkingPaid(p.id)}
                    className="text-green-400 hover:text-green-300 transition-colors"
                    style={{ fontSize: 14 }}
                  >
                    Mark paid
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Create payout modal */}
      {showCreate && selectedArtist && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 px-4">
          <div className="bg-gray-900 border border-gray-700 rounded-xl p-6 w-full max-w-md">
            <h2 className="text-white font-semibold mb-1" style={{ fontSize: 22 }}>
              Create Payout
            </h2>
            <p className="text-gray-400 mb-5" style={{ fontSize: 15 }}>
              {selectedArtist.email} · Available: {fmt(selectedArtist.total_net)}
            </p>

            <div className="space-y-4">
              <div>
                <label>Amount (USD)</label>
                <input
                  type="number"
                  value={payoutAmount}
                  onChange={(e) => setPayoutAmount(e.target.value)}
                  placeholder="0.00"
                  className="w-full bg-gray-800 border border-gray-700 text-white focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div>
                <label>Payment Method</label>
                <select
                  value={payoutMethod}
                  onChange={(e) => setPayoutMethod(e.target.value)}
                  className="w-full bg-gray-800 border border-gray-700 text-white focus:outline-none focus:border-indigo-500"
                >
                  {["zelle", "paypal", "transferencia", "binance", "otro"].map(
                    (m) => (
                      <option key={m} value={m}>
                        {m.charAt(0).toUpperCase() + m.slice(1)}
                      </option>
                    )
                  )}
                </select>
              </div>

              <div>
                <label>Note (optional)</label>
                <input
                  type="text"
                  value={payoutNote}
                  onChange={(e) => setPayoutNote(e.target.value)}
                  placeholder="Q1 2026 royalties..."
                  className="w-full bg-gray-800 border border-gray-700 text-white focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div className="flex gap-3 pt-2">
                <button
                  onClick={() => setShowCreate(false)}
                  className="flex-1 py-2 rounded-md border border-gray-700 text-gray-400 hover:text-white transition-colors"
                  style={{ fontSize: 15 }}
                >
                  Cancel
                </button>
                <button
                  onClick={handleCreatePayout}
                  disabled={creating || !payoutAmount}
                  className="flex-1 py-2 rounded-md bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white font-medium transition-colors"
                  style={{ fontSize: 15 }}
                >
                  {creating ? "Creating..." : "Create Payout"}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Mark paid modal */}
      {markingPaid && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 px-4">
          <div className="bg-gray-900 border border-gray-700 rounded-xl p-6 w-full max-w-sm">
            <h2 className="text-white font-semibold mb-1" style={{ fontSize: 22 }}>
              Mark as Paid
            </h2>
            <p className="text-gray-400 mb-5" style={{ fontSize: 15 }}>
              Enter the transfer confirmation number.
            </p>
            <input
              type="text"
              value={reference}
              onChange={(e) => setReference(e.target.value)}
              placeholder="Confirmation / Reference #"
              className="w-full bg-gray-800 border border-gray-700 text-white focus:outline-none focus:border-indigo-500 mb-4"
            />
            <div className="flex gap-3">
              <button
                onClick={() => setMarkingPaid(null)}
                className="flex-1 py-2 rounded-md border border-gray-700 text-gray-400 hover:text-white transition-colors"
                style={{ fontSize: 15 }}
              >
                Cancel
              </button>
              <button
                onClick={() => handleMarkPaid(markingPaid)}
                disabled={!reference.trim()}
                className="flex-1 py-2 rounded-md bg-green-600 hover:bg-green-500 disabled:opacity-50 text-white font-medium transition-colors"
                style={{ fontSize: 15 }}
              >
                Confirm Paid
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
