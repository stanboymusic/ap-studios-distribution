import { useEffect, useState } from "react";
import { apiFetch } from "../../api/client";

interface Balance {
  total_gross_earned: number;
  total_commission_paid: number;
  total_net_earned: number;
  total_paid_out: number;
  pending_payout: number;
  available_balance: number;
  currency: string;
  statement_count: number;
}

interface Statement {
  id: string;
  release_title: string;
  isrc?: string | null;
  dsp: string;
  territory: string;
  streams: number;
  gross_amount: number;
  net_amount: number;
}

interface Period {
  period: string;
  total_streams: number;
  total_gross: number;
  total_net: number;
  dsps: string[];
  statements?: Statement[];
}

interface Payout {
  id: string;
  amount: number;
  currency: string;
  method: string;
  status: string;
  reference?: string;
  created_at: string;
  paid_at?: string;
}

const DSP_LABELS: Record<string, string> = {
  spotify: "Spotify",
  apple_music: "Apple Music",
  youtube_music: "YouTube Music",
  amazon_music: "Amazon Music",
  deezer: "Deezer",
};

const fmt = (n: number) =>
  new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: 2,
  }).format(n);

export default function EarningsPage() {
  const [balance, setBalance] = useState<Balance | null>(null);
  const [periods, setPeriods] = useState<Period[]>([]);
  const [payouts, setPayouts] = useState<Payout[]>([]);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState<"overview" | "history" | "payouts">(
    "overview"
  );

  useEffect(() => {
    Promise.all([
      apiFetch<Balance>("/royalties/balance"),
      apiFetch<{ periods: Period[] }>("/royalties/statements"),
      apiFetch<{ payouts: Payout[] }>("/royalties/payouts"),
    ])
      .then(([bal, stmts, pays]) => {
        setBalance(bal);
        setPeriods(stmts.periods ?? []);
        setPayouts(pays.payouts ?? []);
      })
      .finally(() => setLoading(false));
  }, []);

  const statusPill: Record<string, string> = {
    pending: "pill-gold",
    paid: "pill-green",
    failed: "pill-wine",
  };

  if (loading) {
    return <div className="p-6 text-gray-400 text-sm">Loading earnings...</div>;
  }

  return (
    <div className="p-6 max-w-5xl mx-auto">
      <h1 className="text-2xl font-bold text-white mb-6">My Earnings</h1>

      {/* Balance cards */}
      {balance && (
        <div className="grid grid-cols-2 gap-4 mb-6 sm:grid-cols-3">
          {[
            {
              label: "Available Balance",
              value: fmt(balance.available_balance),
              highlight: true,
            },
            {
              label: "Total Earned (Net)",
              value: fmt(balance.total_net_earned),
            },
            {
              label: "Total Paid Out",
              value: fmt(balance.total_paid_out),
            },
            {
              label: "Pending Payout",
              value: fmt(balance.pending_payout),
            },
            {
              label: "AP Studios Commission (15%)",
              value: fmt(balance.total_commission_paid),
            },
            {
              label: "Gross from DSPs",
              value: fmt(balance.total_gross_earned),
            },
          ].map(({ label, value, highlight }) => (
            <div
              key={label}
              className={`rounded-[14px] border p-4 ${
                highlight
                  ? "bg-indigo-900/30 border-indigo-500/40"
                  : "bg-gray-900 border-gray-800"
              }`}
            >
              <p
                className="text-gray-500 uppercase mb-1"
                style={{ fontSize: 12, letterSpacing: "0.12em" }}
              >
                {label}
              </p>
              <p
                className={`text-2xl font-bold ${
                  highlight ? "text-indigo-300" : "text-white"
                }`}
              >
                {value}
              </p>
            </div>
          ))}
        </div>
      )}

      {/* Note about payment delays */}
      <div
        className="mb-6 px-4 py-3 bg-blue-900/20 border border-blue-500/20 rounded-lg text-blue-300"
        style={{ fontSize: 14 }}
      >
        Note: DSP royalties typically take 2-3 months to be reported and
        processed. Your balance updates as DSRs are received by AP Studios.
      </div>

      {/* Tabs */}
      <div className="flex gap-1 mb-4 bg-gray-900 rounded-lg p-1 w-fit">
        {(["overview", "history", "payouts"] as const).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`px-5 py-2 rounded-md font-medium transition-colors ${
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

      {/* Overview tab */}
      {tab === "overview" && (
        <div className="space-y-3">
          {periods.length === 0 && (
            <p className="text-gray-500 text-sm">
              No earnings yet. Once your music streams and AP Studios receives
              DSR reports from DSPs, your earnings will appear here.
            </p>
          )}
          {periods.map((p) => (
            <div
              key={p.period}
              className="bg-gray-900 border border-gray-800 rounded-xl px-5 py-4"
            >
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-white font-semibold" style={{ fontSize: 18 }}>
                    {p.period}
                  </p>
                  <p className="text-gray-500 mt-0.5" style={{ fontSize: 14 }}>
                    {p.total_streams.toLocaleString()} streams ·{" "}
                    {(p.dsps ?? []).map((d) => DSP_LABELS[d] ?? d).join(", ")}
                  </p>
                </div>
                <div className="text-right">
                  <p className="text-indigo-300 font-bold" style={{ fontSize: 22 }}>
                    {fmt(p.total_net)}
                  </p>
                  <p className="text-gray-600" style={{ fontSize: 14 }}>
                    gross {fmt(p.total_gross)}
                  </p>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* History tab - detailed statements */}
      {tab === "history" && (
        <div className="space-y-3">
          {periods.flatMap((p) => p.statements ?? []).length === 0 && (
            <p className="text-gray-500 text-sm">No statements yet.</p>
          )}
          {periods.flatMap((p) => p.statements ?? []).map((s) => (
            <div
              key={s.id}
              className="bg-gray-900 border border-gray-800 rounded-lg px-4 py-3 grid grid-cols-12 gap-2 items-center"
            >
              <div className="col-span-4">
                <p className="text-white text-sm truncate">{s.release_title}</p>
                <p className="text-gray-500 font-mono" style={{ fontSize: 14 }}>
                  {s.isrc ?? "-"}
                </p>
              </div>
              <div className="col-span-2 text-gray-400" style={{ fontSize: 14 }}>
                {DSP_LABELS[s.dsp] ?? s.dsp}
              </div>
              <div className="col-span-2 text-gray-400" style={{ fontSize: 14 }}>
                {s.territory}
              </div>
              <div className="col-span-2 text-gray-400" style={{ fontSize: 14 }}>
                {s.streams.toLocaleString()} streams
              </div>
              <div className="col-span-2 text-right">
                <p className="text-indigo-300 text-sm font-medium">
                  {fmt(s.net_amount)}
                </p>
                <p className="text-gray-600" style={{ fontSize: 14 }}>
                  gross {fmt(s.gross_amount)}
                </p>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Payouts tab */}
      {tab === "payouts" && (
        <div className="space-y-3">
          {payouts.length === 0 && (
            <p className="text-gray-500 text-sm">No payouts yet.</p>
          )}
          {payouts.map((p) => (
            <div
              key={p.id}
              className="bg-gray-900 border border-gray-800 rounded-xl px-5 py-4 flex items-center justify-between"
            >
              <div>
                <p className="text-white font-semibold" style={{ fontSize: 18 }}>
                  {fmt(p.amount)}
                </p>
                <p className="text-gray-500 mt-0.5" style={{ fontSize: 14 }}>
                  {p.method.toUpperCase()}
                  {p.reference ? ` · Ref: ${p.reference}` : ""}
                  {" · "}
                  {new Date(p.created_at).toLocaleDateString()}
                </p>
              </div>
              <span
                className={`pill ${statusPill[p.status] ?? statusPill.pending}`}
              >
                {p.status}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
