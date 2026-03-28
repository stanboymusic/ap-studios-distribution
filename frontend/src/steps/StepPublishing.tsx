import { useWizard } from "../app/WizardProvider";

const PUBLISHING_TYPES = [
  { value: "controlled_100", label: "Controlled 100% or administered by my distributor" },
  { value: "not_controlled", label: "Not controlled — someone else administers" },
  { value: "split", label: "Split — I control part of it" },
];

export default function StepPublishing({ onNext, onBack }: { onNext: () => void; onBack: () => void }) {
  const { state, dispatch } = useWizard();
  const tracks = state.tracks || [];

  const getPublishing = (trackId: string) =>
    (state.publishing || []).find((p: any) => p.track_id === trackId) || {
      track_id: trackId,
      track_title: "",
      publishing_type: "controlled_100",
      publisher_name: state.label_name || "AP Studios",
    };

  const updatePublishing = (trackId: string, field: string, value: string) => {
    const current = state.publishing || [];
    const existing = current.find((p: any) => p.track_id === trackId);
    const track = tracks.find((t: any) => (t.track_id || t.id || String(t.track_number)) === trackId);

    const updated = existing
      ? current.map((p: any) => (p.track_id === trackId ? { ...p, [field]: value } : p))
      : [
          ...current,
          {
            track_id: trackId,
            track_title: track?.title || "",
            publishing_type: "controlled_100",
            publisher_name: state.label_name || "AP Studios",
            [field]: value,
          },
        ];

    dispatch({ type: "SET_FIELD", field: "publishing", value: updated });
  };

  return (
    <div style={{ maxWidth: 600, margin: "0 auto" }}>
      <div className="page-eyebrow">Step — Publishing</div>
      <h2 style={{ fontFamily: "var(--font-display)", fontSize: 28, fontWeight: 300, color: "#fff", marginBottom: 6 }}>Publishing Obligations</h2>

      {tracks.length === 0 && <div style={{ textAlign: "center", padding: "40px 20px", color: "var(--mist-d)", fontSize: 14 }}>No tracks added yet. Go back to add tracks first.</div>}

      <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
        {tracks.map((track: any) => {
          const trackId = track.track_id || track.id || String(track.track_number);
          const pub = getPublishing(trackId);
          return (
            <div key={trackId} style={{ background: "var(--card)", border: "0.5px solid var(--border)", borderRadius: 12, padding: "18px 20px" }}>
              <div style={{ fontSize: 15, color: "var(--mist)", fontWeight: 400, marginBottom: 14 }}>{track.title || "Untitled Track"}</div>
              <div style={{ marginBottom: 14 }}>
                <label>Publishing Obligation (US)</label>
                <select value={pub.publishing_type} onChange={(e) => updatePublishing(trackId, "publishing_type", e.target.value)}>
                  {PUBLISHING_TYPES.map((pt) => <option key={pt.value} value={pt.value}>{pt.label}</option>)}
                </select>
              </div>
              <div>
                <label>Publisher / Administrator</label>
                <input value={pub.publisher_name} onChange={(e) => updatePublishing(trackId, "publisher_name", e.target.value)} placeholder="Your publishing company or label name" />
              </div>
            </div>
          );
        })}
      </div>

      <div className="mt-4 flex gap-2">
        <button onClick={onBack} className="btn-ghost">Atrás</button>
        <button onClick={onNext} className="btn-primary">Continuar</button>
      </div>
    </div>
  );
}
