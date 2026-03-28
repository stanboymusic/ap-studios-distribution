import { useWizard } from "../app/WizardProvider";

export default function StepPublishing({ onNext, onBack }: { onNext: () => void; onBack: () => void }) {
  const { state, dispatch } = useWizard();
  const tracks = state.tracks || [];

  const updatePub = (trackId: string, field: string, value: string) => {
    const current = state.publishing || [];
    const existing = current.find((p: any) => p.track_id === trackId);
    const updated = existing
      ? current.map((p: any) => p.track_id === trackId ? { ...p, [field]: value } : p)
      : [...current, { track_id: trackId, track_title: "", publishing_type: "controlled_100", publisher_name: state.label_name || "AP Studios", [field]: value }];
    dispatch({ type: "SET_FIELD", field: "publishing", value: updated });
  };

  return (
    <div style={{ maxWidth: 600, margin: "0 auto" }}>
      <h2>Publishing</h2>
      {tracks.map((t: any, idx: number) => {
        const id = t.track_id || t.id || String(idx + 1);
        const p = (state.publishing || []).find((x: any) => x.track_id === id) || {};
        return (
          <div key={id} style={{ border: "1px solid var(--border)", borderRadius: 8, padding: 12, marginBottom: 10 }}>
            <div>{t.title || "Untitled Track"}</div>
            <select value={p.publishing_type || "controlled_100"} onChange={e => updatePub(id, "publishing_type", e.target.value)}>
              <option value="controlled_100">Controlled 100%</option>
              <option value="not_controlled">Not Controlled</option>
              <option value="split">Split</option>
            </select>
            <input value={p.publisher_name || state.label_name || "AP Studios"} onChange={e => updatePub(id, "publisher_name", e.target.value)} />
          </div>
        );
      })}
      <div className="mt-4 flex gap-2">
        <button onClick={onBack} className="btn-ghost">Atrás</button>
        <button onClick={onNext} className="btn-primary">Continuar</button>
      </div>
    </div>
  );
}
