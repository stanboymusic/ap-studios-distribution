import { useState, useEffect } from "react";
import { apiFetch } from "../api/client";
import { DeliveryOverview } from "../api/schema";
import { Card, CardContent } from "../components/ui/Card";
import { Button } from "../components/ui/Button";
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from "../components/ui/Table";
import RevenueDashboard from "./RevenueDashboard";
import { useAuth } from "../app/auth";

interface ReleaseResponse {
  id: string;
  title: string;
  type: string;
  status: string;
  artist_name?: string;
}

export default function Dashboard({
  onNewRelease,
  onOpenRelease,
}: {
  onNewRelease?: () => void;
  onOpenRelease?: (releaseId: string) => void;
}) {
  const [deliveries, setDeliveries] = useState<DeliveryOverview[]>([]);
  const [releases, setReleases] = useState<ReleaseResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const { user } = useAuth();
  const isAdmin = user?.role === "admin";
  const [activeTab, setActiveTab] = useState<"deliveries" | "releases" | "revenue">(isAdmin ? "deliveries" : "releases");

  useEffect(() => {
    loadData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const relPromise = apiFetch<ReleaseResponse[]>("/releases/");
      const delPromise = isAdmin ? apiFetch<DeliveryOverview[]>("/delivery/overview") : Promise.resolve<DeliveryOverview[]>([]);
      const [delData, relData] = await Promise.all([delPromise, relPromise]);
      setDeliveries(delData || []);
      setReleases(relData || []);
    } catch (error) {
      console.error("Error loading dashboard data:", error);
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    const s = (status || "").toUpperCase();
    switch (s) {
      case "ACCEPTED":
      case "CONFIRMED":
        return "bg-green-500";
      case "REJECTED":
      case "FAILED":
        return "bg-red-500";
      case "PROCESSING":
        return "bg-yellow-500";
      case "UPLOADED":
      case "DELIVERED":
        return "bg-blue-500";
      case "DRAFT":
        return "bg-gray-400";
      default:
        return "bg-gray-300";
    }
  };

  const stats = {
    total: releases.length,
    delivered: isAdmin ? deliveries.length : releases.filter((r) => (r.status || "").toUpperCase() === "DELIVERED").length,
    accepted: isAdmin
      ? deliveries.filter((r) => (r.status || "").toUpperCase() === "ACCEPTED").length
      : releases.filter((r) => (r.status || "").toUpperCase() === "CONFIRMED").length,
  };

  return (
    <div className="p-8 space-y-10">
      <header className="flex justify-between items-end">
        <div>
          <h2 className="font-semibold" style={{ fontSize: 36, fontFamily: "var(--font-display)", color: "#fff" }}>
            {isAdmin ? "Dashboard" : "Artist Portal"}
          </h2>
          <p className="text-sm" style={{ color: "var(--mist-d)" }}>
            {isAdmin ? "Release management and distribution center" : "Manage your releases and track approval status"}
          </p>
        </div>
        <Button className="flex gap-2" onClick={onNewRelease}>
          <span>+</span> New Release
        </Button>
      </header>

      <section className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <StatCard title={isAdmin ? "All Releases" : "My Releases"} value={stats.total} />
        <StatCard title="Delivered" value={stats.delivered} />
        <StatCard title={isAdmin ? "Accepted by DSPs" : "Approved by AP Studios"} value={stats.accepted} />
      </section>

      <section className="space-y-4">
        <div className="flex" style={{ borderBottom: "0.5px solid var(--border)" }}>
          {isAdmin ? (
            <button
              className="px-4 py-2 font-medium text-sm"
              style={activeTab === "deliveries" ? { borderBottom: "2px solid var(--wine-ll)", color: "var(--mist)", background: "rgba(107,26,46,0.15)" } : { color: "var(--mist-d)", background: "transparent" }}
              onClick={() => setActiveTab("deliveries")}
            >
              Recent Deliveries
            </button>
          ) : null}
          <button
            className="px-4 py-2 font-medium text-sm"
            style={activeTab === "releases" ? { borderBottom: "2px solid var(--wine-ll)", color: "var(--mist)", background: "rgba(107,26,46,0.15)" } : { color: "var(--mist-d)", background: "transparent" }}
            onClick={() => setActiveTab("releases")}
          >
            {isAdmin ? "Catalog (All)" : "My Releases"}
          </button>
          {isAdmin ? (
            <button
              className="px-4 py-2 font-medium text-sm"
              style={activeTab === "revenue" ? { borderBottom: "2px solid var(--wine-ll)", color: "var(--mist)", background: "rgba(107,26,46,0.15)" } : { color: "var(--mist-d)", background: "transparent" }}
              onClick={() => setActiveTab("revenue")}
            >
              Financials & Revenue
            </button>
          ) : null}
        </div>

        {isAdmin && activeTab === "revenue" ? (
          <RevenueDashboard />
        ) : (
          <Card className="p-0 overflow-hidden">
            {loading ? (
              <div className="p-8 text-sm" style={{ color: "var(--mist-d)" }}>Loading…</div>
            ) : activeTab === "deliveries" && isAdmin ? (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>ID</TableHead>
                    <TableHead>Title</TableHead>
                    <TableHead>DSP</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Updated</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {deliveries.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={5} className="text-center py-8" style={{ color: "var(--mist-d)" }}>
                        No deliveries found.
                      </TableCell>
                    </TableRow>
                  ) : (
                    deliveries.map((r) => (
                      <TableRow key={r.release_id}>
                        <TableCell className="font-medium font-mono" style={{ color: "var(--mist)" }}>{r.release_id.substring(0, 8)}</TableCell>
                        <TableCell className="font-medium">{r.title}</TableCell>
                        <TableCell>{r.dsp}</TableCell>
                        <TableCell>
                          <div className="flex items-center gap-2">
                            <div className={`w-2 h-2 rounded-full ${getStatusColor(r.status)}`} />
                            <span className="capitalize">{r.status.toLowerCase()}</span>
                          </div>
                        </TableCell>
                        <TableCell style={{ color: "var(--mist-d)" }}>
                          {r.last_event ? new Date(r.last_event).toLocaleDateString() : "N/A"}
                        </TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>ID</TableHead>
                    <TableHead>Title</TableHead>
                    <TableHead>Artist</TableHead>
                    <TableHead>Type</TableHead>
                    <TableHead>Status</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {releases.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={5} className="text-center py-8" style={{ color: "var(--mist-d)" }}>
                        {isAdmin ? "Catalog is empty." : "You do not have releases yet."}
                      </TableCell>
                    </TableRow>
                  ) : (
                    releases.map((r) => (
                      <TableRow
                        key={r.id}
                        className="cursor-pointer"
                        style={{ background: "transparent" }}
                        onClick={() => onOpenRelease?.(r.id)}
                      >
                        <TableCell className="font-medium font-mono" style={{ color: "var(--mist)" }}>{r.id.substring(0, 8)}</TableCell>
                        <TableCell className="font-medium">{r.title}</TableCell>
                        <TableCell>{r.artist_name || "Unknown"}</TableCell>
                        <TableCell>{r.type}</TableCell>
                        <TableCell>
                          <div className="flex items-center gap-2">
                            <div className={`w-2 h-2 rounded-full ${getStatusColor(r.status)}`} />
                            <span className="capitalize">{r.status.toLowerCase()}</span>
                          </div>
                        </TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            )}
          </Card>
        )}
      </section>
    </div>
  );
}

function StatCard({ title, value }: { title: string; value: number }) {
  return (
    <Card>
      <CardContent className="p-7">
        <h2 className="text-sm font-medium" style={{ color: "var(--mist-d)" }}>{title}</h2>
        <p className="font-bold mt-2" style={{ fontSize: 38, color: "var(--mist)" }}>
          {value}
        </p>
      </CardContent>
    </Card>
  );
}
