import { useEffect, useMemo, useState } from "react";
import { apiFetch } from "../api/client";
import { Card, CardContent } from "../components/ui/Card";
import { Button } from "../components/ui/Button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "../components/ui/Table";

type ManualState = "pending" | "approved" | "approved_auto" | "rejected";

type ValidationQueueItem = {
  release_id: string;
  title: string;
  artist_name: string;
  release_status: string;
  delivery_status?: string | null;
  ddex_status?: string | null;
  manual_state: ManualState;
  manual_reason?: string | null;
  manual_actor?: string | null;
  manual_updated_at?: string | null;
  last_validation_at?: string | null;
  upc?: string | null;
};

type ValidationQueueResponse = {
  items: ValidationQueueItem[];
  total: number;
  filter: "all" | "pending" | "approved" | "rejected";
};

type ValidationRun = {
  id: string;
  status: "passed" | "failed";
  validation_type: string;
  validator: string;
  created_at: string;
  errors?: Array<{ message: string }>;
};

type ValidationHistoryResponse = {
  last_status?: string | null;
  runs: ValidationRun[];
};

function StateBadge({ state }: { state: ManualState }) {
  const tone = useMemo(() => {
    if (state === "approved" || state === "approved_auto") return "bg-green-600";
    if (state === "rejected") return "bg-red-600";
    return "bg-yellow-600";
  }, [state]);

  const label = state === "approved_auto" ? "AUTO APPROVED" : state.toUpperCase();
  return <span className={`inline-flex rounded-full px-3 py-1 text-xs font-semibold text-white ${tone}`}>{label}</span>;
}

export default function ValidationCenter({ onOpenRelease }: { onOpenRelease?: (releaseId: string) => void }) {
  const [filter, setFilter] = useState<"all" | "pending" | "approved" | "rejected">("pending");
  const [items, setItems] = useState<ValidationQueueItem[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [history, setHistory] = useState<ValidationRun[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadingHistory, setLoadingHistory] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [reason, setReason] = useState("");
  const [busyAction, setBusyAction] = useState<"approve" | "reject" | "revalidate" | null>(null);

  const selected = selectedId ? items.find((item) => item.release_id === selectedId) || null : null;

  const loadQueue = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await apiFetch<ValidationQueueResponse>(`/validation/admin/queue?state=${filter}`);
      setItems(response.items || []);
      if (response.items?.length) {
        setSelectedId((prev) => prev || response.items[0].release_id);
      } else {
        setSelectedId(null);
      }
    } catch (e: any) {
      setError(e?.message || "Failed to load validation queue");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadQueue();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filter]);

  useEffect(() => {
    let cancelled = false;
    async function loadHistory() {
      if (!selectedId) {
        setHistory([]);
        return;
      }
      setLoadingHistory(true);
      try {
        const response = await apiFetch<ValidationHistoryResponse>(`/validation/history/${selectedId}`);
        if (!cancelled) setHistory((response.runs || []).slice().reverse());
      } catch {
        if (!cancelled) setHistory([]);
      } finally {
        if (!cancelled) setLoadingHistory(false);
      }
    }
    loadHistory();
    return () => {
      cancelled = true;
    };
  }, [selectedId]);

  const runAction = async (action: "approve" | "reject" | "revalidate") => {
    if (!selectedId) return;
    if (action === "reject" && !reason.trim()) {
      alert("Debes indicar una razón para rechazar.");
      return;
    }

    setBusyAction(action);
    try {
      if (action === "revalidate") {
        await apiFetch(`/validation/admin/${selectedId}/revalidate`, { method: "POST" });
      } else {
        await apiFetch(`/validation/admin/${selectedId}/${action}`, {
          method: "POST",
          body: JSON.stringify({
            reason: reason.trim() || undefined,
          }),
        });
      }
      setReason("");
      await loadQueue();
    } catch (e: any) {
      alert(e?.message || "Action failed");
    } finally {
      setBusyAction(null);
    }
  };

  return (
    <div className="p-8 space-y-6">
      <header className="flex items-start justify-between gap-6">
        <div>
          <h2
            className="font-semibold"
            style={{ fontSize: 36, fontFamily: "var(--font-display)", color: "#fff" }}
          >
            Validation Center
          </h2>
          <p className="text-sm" style={{ color: "var(--mist-d)" }}>
            Revisión administrativa manual de envíos DDEX sin usar código.
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="ghost" onClick={loadQueue} disabled={loading}>
            Refresh
          </Button>
        </div>
      </header>

      <section className="flex flex-wrap gap-2">
        <Button variant={filter === "pending" ? "primary" : "outline"} onClick={() => setFilter("pending")}>
          Pending
        </Button>
        <Button variant={filter === "approved" ? "primary" : "outline"} onClick={() => setFilter("approved")}>
          Approved
        </Button>
        <Button variant={filter === "rejected" ? "primary" : "outline"} onClick={() => setFilter("rejected")}>
          Rejected
        </Button>
        <Button variant={filter === "all" ? "primary" : "outline"} onClick={() => setFilter("all")}>
          All
        </Button>
      </section>

      {error ? <div className="text-sm" style={{ color: "var(--wine-ll)" }}>{error}</div> : null}

      <section className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        <Card className="xl:col-span-2 rounded-2xl border-none shadow-sm">
          <CardContent className="p-0">
            {loading ? (
              <div className="p-8 text-sm" style={{ color: "var(--mist-d)" }}>
                Loading validation queue…
              </div>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Release</TableHead>
                    <TableHead>Artist</TableHead>
                    <TableHead>DDEX</TableHead>
                    <TableHead>Manual</TableHead>
                    <TableHead>Delivery</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {items.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={5} className="text-center py-9" style={{ color: "var(--mist-d)" }}>
                        No releases in this filter.
                      </TableCell>
                    </TableRow>
                  ) : (
                    items.map((item) => (
                      <TableRow
                        key={item.release_id}
                        className="cursor-pointer"
                        style={{
                          background:
                            selectedId === item.release_id
                              ? "rgba(107,26,46,0.12)"
                              : "transparent",
                        }}
                        onClick={() => setSelectedId(item.release_id)}
                      >
                        <TableCell>
                          <div className="font-medium">{item.title}</div>
                          <div className="font-mono" style={{ fontSize: 14, color: "var(--mist-d)" }}>
                            {item.release_id.substring(0, 8)}
                          </div>
                        </TableCell>
                        <TableCell>{item.artist_name}</TableCell>
                        <TableCell style={{ fontSize: 14 }}>
                          {(item.ddex_status || "not_validated").toUpperCase()}
                        </TableCell>
                        <TableCell>
                          <StateBadge state={item.manual_state} />
                        </TableCell>
                        <TableCell style={{ fontSize: 14 }}>
                          {(item.delivery_status || "not_delivered").toUpperCase()}
                        </TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>

        <Card className="rounded-2xl border-none shadow-sm">
          <CardContent className="p-7 space-y-5">
            {!selected ? (
              <div className="text-sm" style={{ color: "var(--mist-d)" }}>
                Selecciona un release para moderar.
              </div>
            ) : (
              <>
                <div>
                  <div className="text-sm font-semibold" style={{ color: "var(--mist)" }}>
                    {selected.title}
                  </div>
                  <div className="font-mono mt-1" style={{ fontSize: 14, color: "var(--mist-d)" }}>
                    {selected.release_id}
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-2 text-sm">
                  <div style={{ color: "var(--mist-d)" }}>DDEX</div>
                  <div>{(selected.ddex_status || "not_validated").toUpperCase()}</div>
                  <div style={{ color: "var(--mist-d)" }}>Manual</div>
                  <div>
                    <StateBadge state={selected.manual_state} />
                  </div>
                  <div style={{ color: "var(--mist-d)" }}>UPC</div>
                  <div className="font-mono">{selected.upc || "—"}</div>
                </div>

                <div className="space-y-2">
                  <label style={{ fontSize: 12, color: "var(--mist-d)", letterSpacing: "0.15em" }}>
                    Reason (required for reject)
                  </label>
                  <textarea
                    value={reason}
                    onChange={(e) => setReason(e.target.value)}
                    className="w-full min-h-[92px] rounded-xl px-4 py-3 text-sm"
                    style={{
                      background: "rgba(255,255,255,0.03)",
                      border: "0.5px solid var(--border)",
                      color: "var(--mist)",
                    }}
                    placeholder="Ej: Metadata inconsistente, conflicto legal, etc."
                  />
                </div>

                <div className="grid grid-cols-1 gap-2">
                  <Button onClick={() => runAction("approve")} disabled={busyAction !== null}>
                    {busyAction === "approve" ? "Approving…" : "Approve Manually"}
                  </Button>
                  <Button variant="outline" onClick={() => runAction("revalidate")} disabled={busyAction !== null}>
                    {busyAction === "revalidate" ? "Revalidating…" : "Run DDEX Validation"}
                  </Button>
                  <Button variant="ghost" onClick={() => runAction("reject")} disabled={busyAction !== null}>
                    {busyAction === "reject" ? "Rejecting…" : "Reject"}
                  </Button>
                  <Button variant="secondary" onClick={() => onOpenRelease?.(selected.release_id)}>
                    Open Release Detail
                  </Button>
                </div>
              </>
            )}
          </CardContent>
        </Card>
      </section>

      <section>
        <Card className="rounded-2xl border-none shadow-sm">
          <CardContent className="p-7">
            <h3 className="text-sm font-semibold" style={{ color: "var(--mist)" }}>
              Validation History
            </h3>
            <div className="mt-4 space-y-2">
              {loadingHistory ? (
                <div className="text-sm" style={{ color: "var(--mist-d)" }}>
                  Loading history…
                </div>
              ) : history.length === 0 ? (
                <div className="text-sm" style={{ color: "var(--mist-d)" }}>
                  No validation runs yet.
                </div>
              ) : (
                history.slice(0, 10).map((run) => (
                  <div
                    key={run.id}
                    className="rounded-xl px-4 py-4"
                    style={{ border: "0.5px solid var(--border)" }}
                  >
                    <div className="flex items-center justify-between gap-3">
                      <div className="text-sm font-medium" style={{ color: "var(--mist)" }}>
                        {run.validation_type} · {run.validator}
                      </div>
                      <span className={`font-semibold ${run.status === "passed" ? "text-green-600" : "text-red-600"}`} style={{ fontSize: 14 }}>
                        {run.status.toUpperCase()}
                      </span>
                    </div>
                    <div className="mt-1" style={{ fontSize: 14, color: "var(--mist-d)" }}>
                      {new Date(run.created_at).toLocaleString()}
                    </div>
                    {run.errors && run.errors.length ? (
                      <div className="mt-2" style={{ fontSize: 14, color: "var(--wine-ll)" }}>
                        {run.errors[0]?.message || "Validation error"}
                      </div>
                    ) : null}
                  </div>
                ))
              )}
            </div>
          </CardContent>
        </Card>
      </section>
    </div>
  );
}
