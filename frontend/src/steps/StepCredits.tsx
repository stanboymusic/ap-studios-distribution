import { useMemo, useState } from "react";
import { useWizard } from "../app/WizardProvider";

const CREDIT_ROLES = ["Featuring", "Producer", "Composer", "Remixer", "Mixer", "Engineer"];

export default function StepCredits({ onNext, onBack }: { onNext: () => void; onBack: () => void }) {
  const { state, dispatch } = useWizard();
  const [newCredit, setNewCredit] = useState({ name: "", role: "Featuring" });

  const initialCredits = useMemo(
    () =>
      [
        ...(state.featuring_artists || []).map((n: string) => ({ name: n, role: "Featuring" })),
        state.producer ? { name: state.producer, role: "Producer" } : null,
        state.composer ? { name: state.composer, role: "Composer" } : null,
        state.remixer ? { name: state.remixer, role: "Remixer" } : null,
      ].filter(Boolean) as Array<{ name: string; role: string }>,
    [state.composer, state.featuring_artists, state.producer, state.remixer],
  );
  const [credits, setCredits] = useState<Array<{ name: string; role: string }>>(initialCredits);

  const syncToState = (list: Array<{ name: string; role: string }>) => {
    dispatch({
      type: "SET_FIELD",
      field: "featuring_artists",
      value: list.filter((c) => c.role === "Featuring").map((c) => c.name),
    });
    dispatch({ type: "SET_FIELD", field: "producer", value: list.find((c) => c.role === "Producer")?.name || "" });
    dispatch({ type: "SET_FIELD", field: "composer", value: list.find((c) => c.role === "Composer")?.name || "" });
    dispatch({ type: "SET_FIELD", field: "remixer", value: list.find((c) => c.role === "Remixer")?.name || "" });
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

  const isRemixRelease = (state.release?.title?.text || "").toLowerCase().includes("remix");

  return (
    <div style={{ maxWidth: 560, margin: "0 auto" }}>
      <div className="page-eyebrow">Step — Credits</div>
      <h2 style={{ fontFamily: "var(--font-display)", fontSize: 28, fontWeight: 300, color: "#fff", marginBottom: 6 }}>
        Additional Credits
      </h2>
      <p style={{ color: "var(--mist-d)", fontSize: 14, marginBottom: 28 }}>
        Add featuring artists, producers, composers, and other contributors. This step is optional.
      </p>

      {credits.length > 0 && (
        <div style={{ marginBottom: 20, display: "flex", flexDirection: "column", gap: 8 }}>
          {credits.map((c, i) => (
            <div key={`${c.name}-${c.role}-${i}`} style={{ display: "flex", alignItems: "center", gap: 12, background: "var(--card)", border: "0.5px solid var(--border)", borderRadius: 8, padding: "12px 16px" }}>
              <div style={{ width: 32, height: 32, borderRadius: "50%", background: "linear-gradient(135deg,var(--wine) 0%,var(--plum-ll) 100%)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 11, color: "#fff", flexShrink: 0 }}>
                {c.name.slice(0, 2).toUpperCase()}
              </div>
              <div style={{ flex: 1 }}>
                <div style={{ fontSize: 14, color: "var(--mist)" }}>{c.name}</div>
                <div style={{ fontSize: 12, color: "var(--mist-d)" }}>{c.role}</div>
              </div>
              <button onClick={() => removeCredit(i)} style={{ background: "none", border: "none", color: "var(--wine-ll)", cursor: "pointer", fontSize: 18, lineHeight: 1, padding: "0 4px" }}>×</button>
            </div>
          ))}
        </div>
      )}

      <div style={{ background: "rgba(255,255,255,0.02)", border: "0.5px solid var(--border)", borderRadius: 10, padding: "18px 20px" }}>
        <div style={{ display: "grid", gridTemplateColumns: "1fr auto", gap: 12, marginBottom: 12 }}>
          <div>
            <label>Contributor name</label>
            <input value={newCredit.name} onChange={(e) => setNewCredit((p) => ({ ...p, name: e.target.value }))} placeholder="Artist, producer, composer..." onKeyDown={(e) => e.key === "Enter" && addCredit()} />
          </div>
          <div>
            <label>Role</label>
            <select value={newCredit.role} onChange={(e) => setNewCredit((p) => ({ ...p, role: e.target.value }))} style={{ width: 140 }}>
              {CREDIT_ROLES.filter((role) => role !== "Remixer" || isRemixRelease).map((r) => (
                <option key={r} value={r}>{r}</option>
              ))}
            </select>
          </div>
        </div>
        <button className="btn-ghost" onClick={addCredit} style={{ width: "100%", justifyContent: "center" }}>
          + Add contributor
        </button>
      </div>

      <p style={{ fontSize: 12, color: "var(--mist-d)", marginTop: 12, opacity: 0.7 }}>
        Featuring artists will appear as "ft." in the track title on DSPs.
      </p>

      <div className="mt-4 flex gap-2">
        <button onClick={onBack} className="btn-ghost">Atrás</button>
        <button onClick={onNext} className="btn-primary">Continuar</button>
      </div>
    </div>
  );
}
