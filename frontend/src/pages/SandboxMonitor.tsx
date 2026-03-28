import { useEffect, useMemo, useState } from "react";
import { apiFetch } from "../api/client";
import { Card, CardContent } from "../components/ui/Card";
import { Button } from "../components/ui/Button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "../components/ui/Table";

type DSPMonitorItem = {
  release_id: string;
  status: "incoming" | "processing" | "accepted" | "rejected";
  path: string;
  has_log: boolean;
};

function Badge({ text, tone }: { text: string; tone: "green" | "red" | "blue" | "gray" | "yellow" }) {
  const cls = useMemo(() => {
    switch (tone) {
      case "green":
        return "pill-green";
      case "red":
        return "pill-wine";
      case "blue":
        return "pill-blue";
      case "yellow":
        return "pill-gold";
      default:
        return "pill-gold";
    }
  }, [tone]);
  return <span className={`pill ${cls}`}>{text}</span>;
}

function statusTone(status: DSPMonitorItem["status"]) {
  if (status === "accepted") return "green";
  if (status === "rejected") return "red";
  if (status === "processing") return "yellow";
  if (status === "incoming") return "blue";
  return "gray";
}

export default function SandboxMonitor() {
  const [items, setItems] = useState<DSPMonitorItem[]>([]);
  const [selectedReleaseId, setSelectedReleaseId] = useState<string | null>(null);
  const [logText, setLogText] = useState<string>("");
  const [loading, setLoading] = useState(true);
  const [reason, setReason] = useState("");
  const [actionBusy, setActionBusy] = useState<"approve" | "reject" | null>(null);
  const [error, setError] = useState<string | null>(null);

  const refresh = async () => {
    setLoading(true);
    setError(null);
    try {
      const list = await apiFetch<DSPMonitorItem[]>("/dsp/monitor");
      setItems(list);
      if (!selectedReleaseId && list.length) setSelectedReleaseId(list[0].release_id);
    } catch (e: any) {
      setError(e?.message || "Failed to load DSP monitor");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    refresh();
    const id = setInterval(refresh, 4000);
    return () => clearInterval(id);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    let cancelled = false;
    async function loadLogs() {
      if (!selectedReleaseId) return;
      try {
        const res = await apiFetch<{ log: string }>(`/dsp/logs/${selectedReleaseId}`);
        if (!cancelled) setLogText(res.log || "");
      } catch {
        if (!cancelled) setLogText("");
      }
    }
    loadLogs();
    return () => {
      cancelled = true;
    };
  }, [selectedReleaseId, items]);

  const act = async (type: "approve" | "reject") => {
    if (!selectedReleaseId) return;
    setActionBusy(type);
    try {
      await apiFetch(`/dsp/${type}/${selectedReleaseId}`, {
        method: "POST",
        body: type === "reject" ? JSON.stringify({ reason }) : JSON.stringify({}),
      });
      setReason("");
      await refresh();
    } catch (e: any) {
      alert(e?.message || "Action failed");
    } finally {
      setActionBusy(null);
    }
  };

  const Section = ({ title, children }: { title: string; children: any }) => (
    <Card className="rounded-2xl border-none shadow-sm">
      <CardContent className="p-6">
        <div className="flex items-center justify-between">
          <h3
            className="text-sm font-semibold"
            style={{ color: "var(--mist)", fontFamily: "var(--font-display)" }}
          >
            {title}
          </h3>
        </div>
        <div className="mt-4">{children}</div>
      </CardContent>
    </Card>
  );

  if (loading && !items.length) {
    return <div className="p-8 text-sm text-gray-500">Loading DSP monitor…</div>;
  }

  if (error) {
    return (
      <div className="p-8 space-y-4">
        <div className="text-sm text-red-600">{error}</div>
        <Button onClick={refresh}>Retry</Button>
      </div>
    );
  }

  const rowsIncoming = items.filter((i) => i.status === "incoming");
  const rowsProcessing = items.filter((i) => i.status === "processing");
  const rowsAccepted = items.filter((i) => i.status === "accepted");
  const rowsRejected = items.filter((i) => i.status === "rejected");

  const selected = selectedReleaseId ? items.find((i) => i.release_id === selectedReleaseId) : null;
  const canModerate = selected?.status === "processing";

  return (
    <div className="p-8 space-y-6">
      <header className="flex items-start justify-between gap-6">
        <div>
          <h2
            className="font-semibold"
            style={{ fontSize: 36, fontFamily: "var(--font-display)", color: "#fff" }}
          >
            DSP Sandbox Monitor
          </h2>
          <p className="text-sm" style={{ color: "var(--mist-d)" }}>
            Fuente de verdad: `sandbox-dsp/` (incoming/processing/accepted/rejected/logs)
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="ghost" onClick={refresh}>
            Refresh
          </Button>
        </div>
      </header>

      <section className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        <div className="space-y-6 xl:col-span-2">
          <Section title={`Incoming (${rowsIncoming.length})`}>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Release</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Path</TableHead>
                  <TableHead>Logs</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {rowsIncoming.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={4} className="text-center py-6 text-gray-500">
                      Empty.
                    </TableCell>
                  </TableRow>
                ) : (
                  rowsIncoming.map((r) => (
                    <TableRow
                      key={r.path}
                      className="cursor-pointer"
                      style={{
                        background:
                          selectedReleaseId === r.release_id
                            ? "rgba(107,26,46,0.12)"
                            : "transparent",
                      }}
                      onClick={() => setSelectedReleaseId(r.release_id)}
                    >
                      <TableCell className="font-mono text-sm">{r.release_id.substring(0, 8)}</TableCell>
                      <TableCell>
                        <Badge text={r.status.toUpperCase()} tone={statusTone(r.status)} />
                      </TableCell>
                      <TableCell className="text-sm text-gray-500">{r.path}</TableCell>
                      <TableCell>{r.has_log ? "Yes" : "—"}</TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </Section>

          <Section title={`Processing (${rowsProcessing.length})`}>
            {rowsProcessing.length === 0 ? (
              <div className="text-sm text-gray-500">Empty.</div>
            ) : (
              <div className="space-y-2">
                {rowsProcessing.map((p) => (
                  <button
                    key={p.path}
                    onClick={() => setSelectedReleaseId(p.release_id)}
                    className="w-full text-left rounded-xl px-4 py-3"
                    style={{
                      background:
                        selectedReleaseId === p.release_id
                          ? "rgba(107,26,46,0.12)"
                          : "var(--card)",
                      border: "0.5px solid var(--border)",
                    }}
                  >
                    <div className="flex items-center justify-between">
                      <div className="font-mono text-sm" style={{ color: "var(--mist)" }}>
                        {p.release_id}
                      </div>
                      <Badge text="PROCESSING" tone="yellow" />
                    </div>
                    <div className="text-sm mt-1" style={{ color: "var(--mist-d)" }}>
                      {p.path}
                    </div>
                  </button>
                ))}
              </div>
            )}
          </Section>

          <Section title={`Accepted (${rowsAccepted.length})`}>
            {rowsAccepted.length === 0 ? (
              <div className="text-sm text-gray-500">Empty.</div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {rowsAccepted.map((a) => (
                  <button
                    key={a.path}
                    onClick={() => setSelectedReleaseId(a.release_id)}
                    className="text-left rounded-xl px-4 py-3"
                    style={{
                      background:
                        selectedReleaseId === a.release_id
                          ? "rgba(107,26,46,0.12)"
                          : "var(--card)",
                      border: "0.5px solid var(--border)",
                    }}
                  >
                    <div className="flex items-center justify-between">
                      <div className="font-mono text-sm" style={{ color: "var(--mist)" }}>
                        {a.release_id.substring(0, 8)}
                      </div>
                      <Badge text="ACCEPTED" tone="green" />
                    </div>
                    <div className="text-sm mt-1" style={{ color: "var(--mist-d)" }}>
                      {a.path}
                    </div>
                  </button>
                ))}
              </div>
            )}
          </Section>

          <Section title={`Rejected (${rowsRejected.length})`}>
            {rowsRejected.length === 0 ? (
              <div className="text-sm text-gray-500">Empty.</div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {rowsRejected.map((rj) => (
                  <button
                    key={rj.path}
                    onClick={() => setSelectedReleaseId(rj.release_id)}
                    className="text-left rounded-xl px-4 py-3"
                    style={{
                      background:
                        selectedReleaseId === rj.release_id
                          ? "rgba(107,26,46,0.12)"
                          : "var(--card)",
                      border: "0.5px solid var(--border)",
                    }}
                  >
                    <div className="flex items-center justify-between">
                      <div className="font-mono text-sm" style={{ color: "var(--mist)" }}>
                        {rj.release_id.substring(0, 8)}
                      </div>
                      <Badge text="REJECTED" tone="red" />
                    </div>
                    <div className="text-sm mt-1" style={{ color: "var(--mist-d)" }}>
                      {rj.path}
                    </div>
                  </button>
                ))}
              </div>
            )}
          </Section>
        </div>

        <div className="space-y-6">
          <Section title="Control Panel">
            {!selectedReleaseId ? (
              <div className="text-sm" style={{ color: "var(--mist-d)" }}>
                Select a release.
              </div>
            ) : (
              <div className="space-y-4">
                <div>
                  <div
                    className="text-sm uppercase"
                    style={{ color: "var(--mist-d)", letterSpacing: "0.15em", fontSize: 12 }}
                  >
                    Release ID
                  </div>
                  <div className="font-mono text-sm break-all" style={{ color: "var(--mist)" }}>
                    {selectedReleaseId}
                  </div>
                </div>

                <div>
                  <div
                    className="text-sm uppercase"
                    style={{ color: "var(--mist-d)", letterSpacing: "0.15em", fontSize: 12 }}
                  >
                    DSP Status
                  </div>
                  <div className="mt-1">
                    {selected ? <Badge text={selected.status.toUpperCase()} tone={statusTone(selected.status)} /> : "—"}
                  </div>
                  <div className="text-sm mt-2" style={{ color: "var(--mist-d)" }}>
                    Actions only enabled while status is `processing`.
                  </div>
                </div>

                <div className="space-y-2">
                  <div
                    className="text-sm uppercase"
                    style={{ color: "var(--mist-d)", letterSpacing: "0.15em", fontSize: 12 }}
                  >
                    Reject reason
                  </div>
                  <input
                    value={reason}
                    onChange={(e) => setReason(e.target.value)}
                    placeholder="Reason (required for reject)"
                    className="w-full rounded-xl px-3 py-2 text-sm"
                    style={{
                      background: "rgba(255,255,255,0.03)",
                      border: "0.5px solid var(--border)",
                      color: "var(--mist)",
                    }}
                  />
                  <div className="flex gap-2">
                    <button
                      onClick={() => act("approve")}
                      disabled={actionBusy !== null || !canModerate}
                      className="btn-primary"
                    >
                      {actionBusy === "approve" ? "Approving…" : "Approve"}
                    </button>
                    <button
                      onClick={() => act("reject")}
                      disabled={actionBusy !== null || !canModerate || !reason.trim()}
                      className="btn-ghost"
                      style={{
                        background: "rgba(107,26,46,0.15)",
                        border: "0.5px solid var(--border)",
                        color: "var(--wine-ll)",
                      }}
                    >
                      {actionBusy === "reject" ? "Rejecting…" : "Reject"}
                    </button>
                  </div>
                </div>

                <div className="pt-4" style={{ borderTop: "0.5px solid var(--border)" }}>
                  <div
                    className="text-sm uppercase"
                    style={{ color: "var(--mist-d)", letterSpacing: "0.15em", fontSize: 12 }}
                  >
                    Logs
                  </div>
                  {logText ? (
                    <pre
                      className="mt-2 max-h-[360px] overflow-auto rounded-xl p-3 text-sm"
                      style={{
                        background: "rgba(255,255,255,0.03)",
                        border: "0.5px solid var(--border)",
                        color: "var(--mist)",
                      }}
                    >
                      {logText}
                    </pre>
                  ) : (
                    <div className="text-sm mt-2" style={{ color: "var(--mist-d)" }}>
                      No logs yet.
                    </div>
                  )}
                </div>
              </div>
            )}
          </Section>
        </div>
      </section>
    </div>
  );
}
