import { useEffect, useState } from 'react';
import { apiFetch } from '../api/client';
import { Card, CardContent } from '../components/ui/Card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/Table';

export default function AnalyticsDashboard() {
  const [data, setData] = useState<any | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        const d = await apiFetch<any>('/analytics/overview');
        setData(d);
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  if (loading) return <div className="text-sm" style={{ color: "var(--mist-d)" }}>Loading…</div>;
  if (!data) return <div className="text-sm" style={{ color: "var(--mist-d)" }}>No analytics yet.</div>;

  const byDspEntries = Object.entries(data.by_dsp || {});
  const byTerritoryEntries = Object.entries(data.by_territory || {});

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card
          className="text-white"
          style={{
            background:
              "linear-gradient(135deg, rgba(107,26,46,0.55) 0%, rgba(74,31,82,0.75) 100%)",
            border: "0.5px solid var(--border)",
          }}
        >
          <CardContent className="p-7">
            <h3 className="text-sm font-medium opacity-80">Total Revenue (Analytics)</h3>
            <p className="font-bold mt-2" style={{ fontSize: 38 }}>
              {data.currency} {Number(data.total_revenue || 0).toFixed(6)}
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-7">
            <h3 className="text-sm font-medium" style={{ color: "var(--mist-d)" }}>
              DSPs tracked
            </h3>
            <p className="font-bold mt-2" style={{ fontSize: 38, color: "var(--mist)" }}>
              {byDspEntries.length}
            </p>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card className="p-0 overflow-hidden">
          <div
            className="p-5 border-b text-sm font-medium"
            style={{ borderBottom: "0.5px solid var(--border)", color: "var(--mist)" }}
          >
            Revenue by DSP
          </div>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>DSP</TableHead>
                <TableHead>Revenue</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {byDspEntries.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={2} className="py-7 text-center text-sm" style={{ color: "var(--mist-d)" }}>Empty</TableCell>
                </TableRow>
              ) : (
                byDspEntries.map(([k, v]) => (
                  <TableRow key={k}>
                    <TableCell className="font-medium">{k}</TableCell>
                    <TableCell>{data.currency} {Number(v || 0).toFixed(6)}</TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </Card>

        <Card className="p-0 overflow-hidden">
          <div
            className="p-5 border-b text-sm font-medium"
            style={{ borderBottom: "0.5px solid var(--border)", color: "var(--mist)" }}
          >
            Revenue by Territory
          </div>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Territory</TableHead>
                <TableHead>Revenue</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {byTerritoryEntries.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={2} className="py-7 text-center text-sm" style={{ color: "var(--mist-d)" }}>Empty</TableCell>
                </TableRow>
              ) : (
                byTerritoryEntries.map(([k, v]) => (
                  <TableRow key={k}>
                    <TableCell className="font-medium">{k}</TableCell>
                    <TableCell>{data.currency} {Number(v || 0).toFixed(6)}</TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </Card>
      </div>
    </div>
  );
}
