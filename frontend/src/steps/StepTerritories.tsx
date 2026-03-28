import { useWizard } from "../app/WizardProvider";

export default function StepTerritories({ onNext, onBack }: { onNext: () => void; onBack: () => void }) {
  const { state, dispatch } = useWizard();
  const set = (field: string, value: any) => dispatch({ type: "SET_FIELD", field, value });

  return (
    <div style={{ maxWidth: 600, margin: "0 auto" }}>
      <h2>Territories & Pricing</h2>
      <label>Excluded Territories (comma separated)</label>
      <input
        value={(state.excluded_territories || []).join(", ")}
        onChange={e => set("excluded_territories", e.target.value.split(",").map(s => s.trim()).filter(Boolean))}
      />
      <label>Album Price</label>
      <input value={state.album_price || "Mid/Front"} onChange={e => set("album_price", e.target.value)} />
      <label>Track Price</label>
      <input value={state.track_price || "Mid"} onChange={e => set("track_price", e.target.value)} />
      <label>Preorder Date</label>
      <input type="date" value={state.preorder_date || ""} onChange={e => set("preorder_date", e.target.value)} />
      <label>
        <input type="checkbox" checked={state.preorder_previewable || false} onChange={e => set("preorder_previewable", e.target.checked)} />
        Previewable
      </label>

      <div className="mt-4 flex gap-2">
        <button onClick={onBack} className="btn-ghost">Atrás</button>
        <button onClick={onNext} className="btn-primary">Continuar</button>
      </div>
    </div>
  );
}
