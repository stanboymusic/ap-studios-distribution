import { useState, useEffect } from 'react';
import { apiFetch } from '../api/client';
import { Card, CardContent } from '../components/ui/Card';
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from '../components/ui/Table';

export default function RevenueDashboard() {
  const [ledger, setLedger] = useState<any[]>([]);
  const [balances, setBalances] = useState<{ currency: string; balances: Record<string, number> } | null>(null);
  const [party, setParty] = useState('');
  const [statement, setStatement] = useState<any | null>(null);
  const [statementError, setStatementError] = useState<string | null>(null);
  const [ingestJson, setIngestJson] = useState<string>(
    JSON.stringify(
      [
        {
          dsp: 'spotify',
          release_ref: 'RELEASE_UUID',
          track_ref: null,
          usage_type: 'stream',
          territory: 'US',
          quantity: 1000,
          gross_amount: 12.34,
          currency: 'USD',
          period_start: '2026-02-01',
          period_end: '2026-02-07',
        },
      ],
      null,
      2
    )
  );
  const [ingestStatus, setIngestStatus] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadAll();
  }, []);

  const loadAll = async () => {
    try {
      const [ledgerData, balancesData] = await Promise.all([
        apiFetch<any[]>('/dsr/ledger'),
        apiFetch<{ currency: string; balances: Record<string, number> }>('/dsr/balances'),
      ]);
      setLedger(ledgerData);
      setBalances(balancesData);
    } catch (error) {
      console.error('Error loading ledger:', error);
    } finally {
      setLoading(false);
    }
  };

  const totalRevenue = ledger.reduce((sum, item) => sum + (Number(item.amount) || 0), 0);

  const loadStatement = async () => {
    setStatement(null);
    setStatementError(null);
    const p = party.trim();
    if (!p) return;
    try {
      const data = await apiFetch<any>(`/dsr/statements/${encodeURIComponent(p)}`);
      setStatement(data);
    } catch (e: any) {
      setStatementError(e?.message || 'No se pudo cargar el statement');
    }
  };

  const ingest = async () => {
    setIngestStatus(null);
    try {
      const payload = JSON.parse(ingestJson);
      const res = await apiFetch<any>('/dsr/ingest', { method: 'POST', body: JSON.stringify(payload) });
      setIngestStatus(`OK: events=${res.events_ingested}, line_items=${res.line_items_generated}`);
      await loadAll();
    } catch (e: any) {
      setIngestStatus(`ERROR: ${e?.message || 'No se pudo ingerir'}`);
    }
  };

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card className="bg-[#1B4079] text-white">
          <CardContent className="p-6">
            <h3 className="text-sm font-medium opacity-80">Total Distributed Revenue</h3>
            <p className="text-4xl font-bold mt-2">
              {balances?.currency || 'USD'} {totalRevenue.toFixed(6)}
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6">
            <h3 className="text-sm font-medium text-[#4D7C8A]">Transactions Count</h3>
            <p className="text-4xl font-bold text-[#1B4079] mt-2">{ledger.length}</p>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardContent className="p-6 space-y-3">
          <div className="text-sm font-medium">Ingest DSR (JSON normalizado)</div>
          <div className="text-xs text-gray-600">
            Pega una lista de items. Asegúrate de que exista una configuración de derechos (splits 100%) para el
            `release_ref` (y opcionalmente `track_ref`).
          </div>
          <textarea
            value={ingestJson}
            onChange={(e) => setIngestJson(e.target.value)}
            className="w-full border rounded px-3 py-2 text-xs font-mono min-h-[160px]"
          />
          <div className="flex items-center gap-3">
            <button onClick={ingest} className="px-4 py-2 rounded bg-[#1B4079] text-white text-sm">
              Ingest
            </button>
            {ingestStatus ? <div className="text-sm">{ingestStatus}</div> : null}
          </div>

          <div className="flex flex-col md:flex-row gap-3 md:items-end">
            <div className="flex-1">
              <label className="block text-sm text-gray-600">Party Reference (para Statement)</label>
              <input
                value={party}
                onChange={(e) => setParty(e.target.value)}
                className="mt-1 w-full border rounded px-3 py-2 text-sm"
                placeholder="Ej: P-ARTIST-1"
              />
            </div>
            <button
              onClick={loadStatement}
              className="px-4 py-2 rounded bg-[#1B4079] text-white text-sm"
            >
              Ver Statement
            </button>
          </div>
          {statementError ? <div className="text-sm text-red-600">{statementError}</div> : null}
          {statement ? (
            <div className="text-sm">
              <div className="font-medium">Total: {statement.currency} {Number(statement.total_amount || 0).toFixed(6)}</div>
              <div className="text-gray-600">Periodo: {statement.period_start} → {statement.period_end}</div>
            </div>
          ) : null}
        </CardContent>
      </Card>

      <Card className="p-0 overflow-hidden">
        {loading ? (
          <div className="p-8 text-sm text-gray-500">Loading…</div>
        ) : (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Party</TableHead>
              <TableHead>Role</TableHead>
              <TableHead>DSP</TableHead>
              <TableHead>Usage</TableHead>
              <TableHead>Territory</TableHead>
              <TableHead>Amount</TableHead>
              <TableHead>Period</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {ledger.length === 0 ? (
              <TableRow>
                <TableCell colSpan={7} className="text-center py-8 text-gray-500">
                  No revenue data available yet.
                </TableCell>
              </TableRow>
            ) : (
              ledger.map((item, index) => (
                <TableRow key={index}>
                  <TableCell className="font-medium">{item.party_reference}</TableCell>
                  <TableCell className="text-xs text-gray-700">{item.role}</TableCell>
                  <TableCell className="text-xs text-gray-700">{item.dsp}</TableCell>
                  <TableCell className="text-xs text-gray-700">{item.usage_type}</TableCell>
                  <TableCell className="text-xs text-gray-700">{item.territory}</TableCell>
                  <TableCell className="font-bold text-green-700">
                    {item.currency} {Number(item.amount || 0).toFixed(6)}
                  </TableCell>
                  <TableCell className="text-xs text-gray-600">{item.period_start} → {item.period_end}</TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
        )}
      </Card>
    </div>
  );
}
