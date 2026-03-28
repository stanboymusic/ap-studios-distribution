import { useWizard } from "../app/WizardProvider";

const GENRES = ["Latin Music","Pop","Rock","Hip-Hop/Rap","R&B/Soul","Electronic/Dance","Classical","Jazz","Reggae","Country","Folk","World Music","Gospel/Christian","Instrumental","Other"];
const META_LANGUAGES = ["Spanish; Castilian","English","Portuguese","French","Italian","German","Japanese","Korean","Instrumental"];

export default function StepGenre({ onNext, onBack }: { onNext: () => void; onBack: () => void }) {
  const { state, dispatch } = useWizard();
  const set = (field: string, value: any) => dispatch({ type: "SET_FIELD", field, value });
  const y = new Date().getFullYear();

  return (
    <div style={{ maxWidth: 560, margin: "0 auto" }}>
      <h2>Genre & Label</h2>
      <label>Primary Genre</label>
      <select value={state.genre || ""} onChange={e => set("genre", e.target.value)}>
        <option value="">Select...</option>{GENRES.map(g => <option key={g}>{g}</option>)}
      </select>

      <label>Meta Language</label>
      <select value={state.meta_language || "Spanish; Castilian"} onChange={e => set("meta_language", e.target.value)}>
        {META_LANGUAGES.map(l => <option key={l}>{l}</option>)}
      </select>

      <label>Label Name</label>
      <input value={state.label_name || ""} onChange={e => set("label_name", e.target.value)} />

      <label>(C) Line</label>
      <input value={state.c_line || `${y} ${state.label_name || "AP Studios"}`} onChange={e => set("c_line", e.target.value)} />

      <label>(P) Line</label>
      <input value={state.p_line || `${y} ${state.label_name || "AP Studios"}`} onChange={e => set("p_line", e.target.value)} />

      <div className="mt-4 flex gap-2">
        <button onClick={onBack} className="btn-ghost">Atrás</button>
        <button onClick={onNext} className="btn-primary">Continuar</button>
      </div>
    </div>
  );
}
