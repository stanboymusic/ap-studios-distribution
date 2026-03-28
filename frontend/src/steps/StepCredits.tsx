import { useMemo, useState } from "react";
import { useWizard } from "../app/WizardProvider";

const CREDIT_ROLES = ["Featuring", "Producer", "Composer", "Remixer", "Mixer", "Engineer"];

export default function StepCredits({ onNext, onBack }: { onNext: () => void; onBack: () => void }) {
  const { state, dispatch } = useWizard();
  const [newCredit, setNewCredit] = useState({ name: "", role: "Featuring" });

  const initialCredits = useMemo(() =>
    [
      ...(state.featuring_artists || []).map((n: string) => ({ name: n, role: "Featuring" })),
      state.producer ? { name: state.producer, role: "Producer" } : null,
      state.composer ? { name: state.composer, role: "Composer" } : null,
      state.remixer ? { name: state.remixer, role: "Remixer" } : null,
    ].filter(Boolean) as Array<{ name: string; role: string }>
  , [state]);

  const [credits, setCredits] = useState<Array<{ name: string; role: string }>>(initialCredits);

  const syncToState = (list: Array<{ name: string; role: string }>) => {
    dispatch({ type: "SET_FIELD", field: "featuring_artists", value: list.filter(c => c.role === "Featuring").map(c => c.name) });
    dispatch({ type: "SET_FIELD", field: "producer", value: list.find(c => c.role === "Producer")?.name || "" });
    dispatch({ type: "SET_FIELD", field: "composer", value: list.find(c => c.role === "Composer")?.name || "" });
    dispatch({ type: "SET_FIELD", field: "remixer", value: list.find(c => c.role === "Remixer")?.name || "" });
  };

  const addCredit = () => {
    if (!newCredit.name.trim()) return;
    const updated = [...credits, { ...newCredit, name: newCredit.name.trim() }];
    setCredits(updated);
    syncToState(updated);
    setNewCredit({ name: "", role: "Featuring" });
  };

  const removeCredit = (idx: number) => {
    const updated = credits.filter((_, i) => i !== idx);
    setCredits(updated);
    syncToState(updated);
  };

  return (
    <div style={{ maxWidth: 560, margin: "0 auto" }}>
      <h2>Additional Credits</h2>
      <div style={{ display: "flex", flexDirection: "column", gap: 8, marginBottom: 12 }}>
        {credits.map((c, i) => (
          <div key={i} style={{ display: "flex", justifyContent: "space-between", border: "1px solid var(--border)", padding: 8, borderRadius: 8 }}>
            <span>{c.name} · {c.role}</span>
            <button onClick={() => removeCredit(i)}>×</button>
          </div>
        ))}
      </div>
      <input value={newCredit.name} onChange={e => setNewCredit(p => ({ ...p, name: e.target.value }))} placeholder="Contributor name" />
      <select value={newCredit.role} onChange={e => setNewCredit(p => ({ ...p, role: e.target.value }))}>
        {CREDIT_ROLES.map(r => <option key={r} value={r}>{r}</option>)}
      </select>
      <button onClick={addCredit}>+ Add contributor</button>
      <div className="mt-4 flex gap-2">
        <button onClick={onBack} className="btn-ghost">Atrás</button>
        <button onClick={onNext} className="btn-primary">Continuar</button>
      </div>
    </div>
  );
}
