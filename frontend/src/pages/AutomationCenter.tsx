import { useEffect, useState } from 'react';
import { apiFetch } from '../api/client';
import { Card, CardContent } from '../components/ui/Card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/Table';

type Settings = {
  enabled: boolean;
  rules: Record<string, boolean>;
  payout_threshold: number;
};

export default function AutomationCenter() {
  const [settings, setSettings] = useState<Settings | null>(null);
  const [logs, setLogs] = useState<any[]>([]);
  const [saving, setSaving] = useState(false);

  async function load() {
    const [s, l] = await Promise.all([
      apiFetch<Settings>('/automation/settings'),
      apiFetch<any[]>('/automation/logs'),
    ]);
    setSettings(s);
    setLogs(l);
  }

  useEffect(() => {
    load().catch(console.error);
  }, []);

  const toggle = async (key: string) => {
    if (!settings) return;
    const next: Settings = {
      ...settings,
      rules: { ...settings.rules, [key]: !settings.rules[key] },
    };
    setSettings(next);
    setSaving(true);
    try {
      await apiFetch<Settings>('/automation/settings', { method: 'POST', body: JSON.stringify(next) });
    } finally {
      setSaving(false);
    }
  };

  const toggleEnabled = async () => {
    if (!settings) return;
    const next: Settings = { ...settings, enabled: !settings.enabled };
    setSettings(next);
    setSaving(true);
    try {
      await apiFetch<Settings>('/automation/settings', { method: 'POST', body: JSON.stringify(next) });
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="p-8 space-y-6">
      <div className="flex items-end justify-between">
        <div>
          <h2
            className="font-semibold"
            style={{ fontSize: 36, fontFamily: "var(--font-display)", color: "#fff" }}
          >
            Automation Center
          </h2>
          <p className="text-sm" style={{ color: "var(--mist-d)" }}>
            Rules, executions, and audit trail (per tenant)
          </p>
        </div>
        <button
          onClick={() => load().catch(console.error)}
          className="btn-ghost"
        >
          Refresh
        </button>
      </div>

      <Card>
        <CardContent className="p-6 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-sm font-medium" style={{ color: "var(--mist)" }}>
                Engine
              </div>
              <div className="text-sm" style={{ color: "var(--mist-d)" }}>
                Global kill-switch for this tenant.
              </div>
            </div>
            <button
              onClick={toggleEnabled}
              className="px-3 py-2 rounded text-sm"
              style={{
                background: settings?.enabled ? "var(--wine)" : "rgba(107,26,46,0.2)",
                color: settings?.enabled ? "#fff" : "var(--mist)",
                border: "0.5px solid var(--border)",
              }}
              disabled={!settings || saving}
            >
              {settings?.enabled ? 'ENABLED' : 'DISABLED'}
            </button>
          </div>

          <div className="pt-4" style={{ borderTop: "0.5px solid var(--border)" }}>
            <div className="text-sm font-medium mb-2" style={{ color: "var(--mist)" }}>
              Rules
            </div>
            {settings ? (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {Object.keys(settings.rules || {}).map((k) => (
                  <button
                    key={k}
                    onClick={() => toggle(k)}
                    className="flex items-center justify-between rounded px-3 py-2 text-sm"
                    style={{
                      background: "var(--card)",
                      border: "0.5px solid var(--border)",
                      color: "var(--mist)",
                    }}
                    disabled={saving}
                  >
                    <span className="font-mono text-sm">{k}</span>
                    <span
                      className={settings.rules[k] ? 'font-medium' : ''}
                      style={{ color: settings.rules[k] ? "var(--success)" : "var(--mist-d)" }}
                    >
                      {settings.rules[k] ? 'ON' : 'OFF'}
                    </span>
                  </button>
                ))}
              </div>
            ) : (
              <div className="text-sm" style={{ color: "var(--mist-d)" }}>
                Loading…
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      <Card className="p-0 overflow-hidden">
        <div
          className="p-4 border-b text-sm font-medium"
          style={{ borderBottom: "0.5px solid var(--border)", color: "var(--mist)" }}
        >
          Execution Logs
        </div>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Time</TableHead>
              <TableHead>Event</TableHead>
              <TableHead>Rule</TableHead>
              <TableHead>Action</TableHead>
              <TableHead>Result</TableHead>
              <TableHead>Message</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {logs.length === 0 ? (
              <TableRow>
                <TableCell colSpan={6} className="py-8 text-center text-sm text-gray-500">
                  No automation logs yet.
                </TableCell>
              </TableRow>
            ) : (
              logs.map((l) => (
                <TableRow key={l.id}>
                  <TableCell className="text-sm">{l.created_at}</TableCell>
                  <TableCell className="text-sm font-mono">{l.event_type}</TableCell>
                  <TableCell className="text-sm font-mono">{l.rule}</TableCell>
                  <TableCell className="text-sm">{l.action}</TableCell>
                  <TableCell className="font-medium" style={{ color: l.success ? "var(--success)" : "var(--wine-ll)" }}>
                    {l.success ? 'OK' : 'FAIL'}
                  </TableCell>
                  <TableCell className="text-sm">{l.message}</TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </Card>
    </div>
  );
}
