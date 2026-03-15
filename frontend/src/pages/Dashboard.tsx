import { useState, useEffect } from "react";
import { apiFetch } from "../api/client";
import { DeliveryOverview } from "../api/schema";
import { Card, CardContent } from "../components/ui/Card";
import { Button } from "../components/ui/Button";
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from "../components/ui/Table";
import RevenueDashboard from "./RevenueDashboard";
import { isAdminRole } from "../app/auth";

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
  const isAdmin = isAdminRole();
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
          <h2 className="text-3xl font-semibold text-[#1B4079]">{isAdmin ? "Dashboard" : "Artist Portal"}</h2>
          <p className="text-sm text-[#4D7C8A]">
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
        <div className="flex border-b border-gray-200">
          {isAdmin ? (
            <button
              className={`px-4 py-2 font-medium text-sm ${activeTab === "deliveries" ? "border-b-2 border-[#1B4079] text-[#1B4079]" : "text-gray-500"}`}
              onClick={() => setActiveTab("deliveries")}
            >
              Recent Deliveries
            </button>
          ) : null}
          <button
            className={`px-4 py-2 font-medium text-sm ${activeTab === "releases" ? "border-b-2 border-[#1B4079] text-[#1B4079]" : "text-gray-500"}`}
            onClick={() => setActiveTab("releases")}
          >
            {isAdmin ? "Catalog (All)" : "My Releases"}
          </button>
          {isAdmin ? (
            <button
              className={`px-4 py-2 font-medium text-sm ${activeTab === "revenue" ? "border-b-2 border-[#1B4079] text-[#1B4079]" : "text-gray-500"}`}
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
              <div className="p-8 text-sm text-gray-500">Loading…</div>
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
                      <TableCell colSpan={5} className="text-center py-8 text-gray-500">
                        No deliveries found.
                      </TableCell>
                    </TableRow>
                  ) : (
                    deliveries.map((r) => (
                      <TableRow key={r.release_id}>
                        <TableCell className="font-medium text-[#1B4079]">{r.release_id.substring(0, 8)}</TableCell>
                        <TableCell className="font-medium">{r.title}</TableCell>
                        <TableCell>{r.dsp}</TableCell>
                        <TableCell>
                          <div className="flex items-center gap-2">
                            <div className={`w-2 h-2 rounded-full ${getStatusColor(r.status)}`} />
                            <span className="capitalize">{r.status.toLowerCase()}</span>
                          </div>
                        </TableCell>
                        <TableCell className="text-[#4D7C8A]">
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
                      <TableCell colSpan={5} className="text-center py-8 text-gray-500">
                        {isAdmin ? "Catalog is empty." : "You do not have releases yet."}
                      </TableCell>
                    </TableRow>
                  ) : (
                    releases.map((r) => (
                      <TableRow
                        key={r.id}
                        className="cursor-pointer hover:bg-gray-50"
                        onClick={() => onOpenRelease?.(r.id)}
                      >
                        <TableCell className="font-medium text-[#1B4079]">{r.id.substring(0, 8)}</TableCell>
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
    <Card className="rounded-2xl border-none shadow-sm">
      <CardContent className="p-6">
        <h2 className="text-sm font-medium text-[#4D7C8A]">{title}</h2>
        <p className="text-3xl font-bold text-[#1B4079] mt-2">{value}</p>
      </CardContent>
    </Card>
  );
}

