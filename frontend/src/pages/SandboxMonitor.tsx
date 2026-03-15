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
        return "bg-green-600";
      case "red":
        return "bg-red-600";
      case "blue":
        return "bg-blue-600";
      case "yellow":
        return "bg-yellow-600";
      default:
        return "bg-gray-500";
    }
  }, [tone]);
  return <span className={`inline-flex rounded-full px-3 py-1 text-xs font-semibold text-white ${cls}`}>{text}</span>;
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
          <h3 className="text-sm font-semibold text-[#1B4079]">{title}</h3>
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
          <h2 className="text-3xl font-semibold text-[#1B4079]">DSP Sandbox Monitor</h2>
          <p className="text-sm text-[#4D7C8A]">Fuente de verdad: `sandbox-dsp/` (incoming/processing/accepted/rejected/logs)</p>
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
                      className={`cursor-pointer ${selectedReleaseId === r.release_id ? "bg-[#F2F6F7]" : ""}`}
                      onClick={() => setSelectedReleaseId(r.release_id)}
                    >
                      <TableCell className="font-mono text-xs">{r.release_id.substring(0, 8)}</TableCell>
                      <TableCell>
                        <Badge text={r.status.toUpperCase()} tone={statusTone(r.status)} />
                      </TableCell>
                      <TableCell className="text-xs text-gray-500">{r.path}</TableCell>
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
                    className={`w-full text-left rounded-xl border border-gray-100 px-4 py-3 hover:bg-gray-50 ${
                      selectedReleaseId === p.release_id ? "bg-[#F2F6F7]" : "bg-white"
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <div className="font-mono text-xs text-[#1B4079]">{p.release_id}</div>
                      <Badge text="PROCESSING" tone="yellow" />
                    </div>
                    <div className="text-xs text-gray-500 mt-1">{p.path}</div>
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
                    className={`text-left rounded-xl border border-gray-100 px-4 py-3 hover:bg-gray-50 ${
                      selectedReleaseId === a.release_id ? "bg-[#F2F6F7]" : "bg-white"
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <div className="font-mono text-xs text-[#1B4079]">{a.release_id.substring(0, 8)}</div>
                      <Badge text="ACCEPTED" tone="green" />
                    </div>
                    <div className="text-xs text-gray-500 mt-1">{a.path}</div>
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
                    className={`text-left rounded-xl border border-gray-100 px-4 py-3 hover:bg-gray-50 ${
                      selectedReleaseId === rj.release_id ? "bg-[#F2F6F7]" : "bg-white"
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <div className="font-mono text-xs text-[#1B4079]">{rj.release_id.substring(0, 8)}</div>
                      <Badge text="REJECTED" tone="red" />
                    </div>
                    <div className="text-xs text-gray-500 mt-1">{rj.path}</div>
                  </button>
                ))}
              </div>
            )}
          </Section>
        </div>

        <div className="space-y-6">
          <Section title="Control Panel">
            {!selectedReleaseId ? (
              <div className="text-sm text-gray-500">Select a release.</div>
            ) : (
              <div className="space-y-4">
                <div>
                  <div className="text-xs text-[#4D7C8A]">Release ID</div>
                  <div className="font-mono text-xs text-gray-900 break-all">{selectedReleaseId}</div>
                </div>

                <div>
                  <div className="text-xs text-[#4D7C8A]">DSP Status</div>
                  <div className="mt-1">
                    {selected ? <Badge text={selected.status.toUpperCase()} tone={statusTone(selected.status)} /> : "—"}
                  </div>
                  <div className="text-xs text-gray-500 mt-2">Actions only enabled while status is `processing`.</div>
                </div>

                <div className="space-y-2">
                  <div className="text-xs text-[#4D7C8A]">Reject reason</div>
                  <input
                    value={reason}
                    onChange={(e) => setReason(e.target.value)}
                    placeholder="Reason (required for reject)"
                    className="w-full rounded-xl border border-gray-200 bg-white px-3 py-2 text-sm"
                  />
                  <div className="flex gap-2">
                    <Button onClick={() => act("approve")} disabled={actionBusy !== null || !canModerate}>
                      {actionBusy === "approve" ? "Approving…" : "Approve"}
                    </Button>
                    <Button variant="ghost" onClick={() => act("reject")} disabled={actionBusy !== null || !canModerate || !reason.trim()}>
                      {actionBusy === "reject" ? "Rejecting…" : "Reject"}
                    </Button>
                  </div>
                </div>

                <div className="border-t border-gray-100 pt-4">
                  <div className="text-xs text-[#4D7C8A]">Logs</div>
                  {logText ? (
                    <pre className="mt-2 max-h-[360px] overflow-auto rounded-xl bg-[#0B1020] text-[#EAF0F2] p-3 text-xs">
                      {logText}
                    </pre>
                  ) : (
                    <div className="text-sm text-gray-500 mt-2">No logs yet.</div>
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

