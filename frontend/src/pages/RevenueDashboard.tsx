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
        <Card
          style={{
            background: "linear-gradient(135deg, rgba(107,26,46,0.55) 0%, rgba(74,31,82,0.75) 100%)",
            border: "0.5px solid var(--border)",
          }}
        >
          <CardContent className="p-7">
            <h3 className="text-sm font-medium" style={{ color: "rgba(255,255,255,0.8)" }}>Total Distributed Revenue</h3>
            <p className="font-bold mt-2" style={{ fontSize: 38, color: "#fff" }}>
              {balances?.currency || 'USD'} {totalRevenue.toFixed(6)}
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-7">
            <h3 className="text-sm font-medium" style={{ color: "var(--mist-d)" }}>Transactions Count</h3>
            <p className="font-bold mt-2" style={{ fontSize: 38, color: "var(--mist)" }}>
              {ledger.length}
            </p>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardContent className="p-7 space-y-3">
          <div className="text-sm font-medium">Ingest DSR (JSON normalizado)</div>
          <div className="text-sm" style={{ color: "var(--mist-d)" }}>
            Pega una lista de items. Asegúrate de que exista una configuración de derechos (splits 100%) para el
            `release_ref` (y opcionalmente `track_ref`).
          </div>
          <textarea
            value={ingestJson}
            onChange={(e) => setIngestJson(e.target.value)}
            className="w-full min-h-[160px] rounded-xl px-4 py-3 text-sm font-mono"
            style={{
              background: "rgba(255,255,255,0.03)",
              border: "0.5px solid var(--border)",
              color: "var(--mist)",
            }}
          />
          <div className="flex items-center gap-3">
            <button onClick={ingest} className="btn-primary">
              Ingest
            </button>
            {ingestStatus ? <div className="text-sm">{ingestStatus}</div> : null}
          </div>

          <div className="flex flex-col md:flex-row gap-3 md:items-end">
            <div className="flex-1">
              <label className="block text-sm" style={{ color: "var(--mist-d)" }}>Party Reference (para Statement)</label>
              <input
                value={party}
                onChange={(e) => setParty(e.target.value)}
                className="mt-1 w-full"
                placeholder="Ej: P-ARTIST-1"
              />
            </div>
            <button
              onClick={loadStatement}
              className="btn-primary"
            >
              Ver Statement
            </button>
          </div>
          {statementError ? <div className="text-sm" style={{ color: "var(--wine-ll)" }}>{statementError}</div> : null}
          {statement ? (
            <div className="text-sm">
              <div className="font-medium" style={{ color: "var(--mist)" }}>Total: {statement.currency} {Number(statement.total_amount || 0).toFixed(6)}</div>
              <div style={{ color: "var(--mist-d)" }}>Periodo: {statement.period_start} → {statement.period_end}</div>
            </div>
          ) : null}
        </CardContent>
      </Card>

      <Card className="p-0 overflow-hidden">
        {loading ? (
          <div className="p-[36px] text-sm" style={{ color: "var(--mist-d)" }}>Loading…</div>
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
                <TableCell colSpan={7} className="text-center py-9" style={{ color: "var(--mist-d)" }}>
                  No revenue data available yet.
                </TableCell>
              </TableRow>
            ) : (
              ledger.map((item, index) => (
                <TableRow key={index}>
                  <TableCell className="font-medium">{item.party_reference}</TableCell>
                  <TableCell className="text-sm" style={{ color: "var(--mist-d)" }}>{item.role}</TableCell>
                  <TableCell className="text-sm" style={{ color: "var(--mist-d)" }}>{item.dsp}</TableCell>
                  <TableCell className="text-sm" style={{ color: "var(--mist-d)" }}>{item.usage_type}</TableCell>
                  <TableCell className="text-sm" style={{ color: "var(--mist-d)" }}>{item.territory}</TableCell>
                  <TableCell className="font-bold" style={{ color: "var(--success)" }}>
                    {item.currency} {Number(item.amount || 0).toFixed(6)}
                  </TableCell>
                  <TableCell className="text-sm" style={{ color: "var(--mist-d)" }}>{item.period_start} → {item.period_end}</TableCell>
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
