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

  if (loading) return <div className="text-sm text-gray-500">Loading…</div>;
  if (!data) return <div className="text-sm text-gray-500">No analytics yet.</div>;

  const byDspEntries = Object.entries(data.by_dsp || {});
  const byTerritoryEntries = Object.entries(data.by_territory || {});

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card className="bg-[#1B4079] text-white">
          <CardContent className="p-6">
            <h3 className="text-sm font-medium opacity-80">Total Revenue (Analytics)</h3>
            <p className="text-4xl font-bold mt-2">
              {data.currency} {Number(data.total_revenue || 0).toFixed(6)}
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6">
            <h3 className="text-sm font-medium text-[#4D7C8A]">DSPs tracked</h3>
            <p className="text-4xl font-bold text-[#1B4079] mt-2">{byDspEntries.length}</p>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card className="p-0 overflow-hidden">
          <div className="p-4 border-b text-sm font-medium">Revenue by DSP</div>
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
                  <TableCell colSpan={2} className="py-6 text-center text-sm text-gray-500">Empty</TableCell>
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
          <div className="p-4 border-b text-sm font-medium">Revenue by Territory</div>
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
                  <TableCell colSpan={2} className="py-6 text-center text-sm text-gray-500">Empty</TableCell>
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

