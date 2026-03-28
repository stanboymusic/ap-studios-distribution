import { useWizard } from "../app/WizardProvider";

const GENRES = [
  "Latin Music", "Pop", "Rock", "Hip-Hop/Rap", "R&B/Soul",
  "Electronic/Dance", "Classical", "Jazz", "Reggae", "Country",
  "Folk", "World Music", "Gospel/Christian", "Instrumental", "Other",
];

const SUBGENRES: Record<string, string[]> = {
  "Latin Music": ["Reggaeton", "Salsa", "Bachata", "Cumbia", "Merengue", "Afro-Brazilian", "Latin Pop", "Latin Trap", "Vallenato"],
  Pop: ["Dance Pop", "Indie Pop", "Synthpop", "K-Pop", "Electropop"],
  "Hip-Hop/Rap": ["Trap", "Drill", "Boom Bap", "Conscious Rap", "Mumble Rap"],
  "Electronic/Dance": ["House", "Techno", "Dubstep", "Drum & Bass", "Ambient"],
};

const META_LANGUAGES = ["Spanish; Castilian", "English", "Portuguese", "French", "Italian", "German", "Japanese", "Korean", "Instrumental"];

export default function StepGenre({ onNext, onBack }: { onNext: () => void; onBack: () => void }) {
  const { state, dispatch } = useWizard();
  const set = (field: string, value: any) => dispatch({ type: "SET_FIELD", field, value });

  const currentYear = new Date().getFullYear();

  return (
    <div style={{ maxWidth: 560, margin: "0 auto" }}>
      <div className="page-eyebrow">Step — Genre & Label</div>
      <h2 style={{ fontFamily: "var(--font-display)", fontSize: 28, fontWeight: 300, color: "#fff", marginBottom: 6 }}>Genre & Label Info</h2>
      <p style={{ color: "var(--mist-d)", fontSize: 14, marginBottom: 28 }}>This metadata determines how DSPs categorize your release.</p>

      <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14 }}>
          <div>
            <label>Primary Genre *</label>
            <select value={state.genre || ""} onChange={(e) => { set("genre", e.target.value); set("subgenre", ""); }}>
              <option value="">Select genre...</option>
              {GENRES.map((g) => <option key={g} value={g}>{g}</option>)}
            </select>
          </div>
          <div>
            <label>Subgenre</label>
            <select value={state.subgenre || ""} onChange={(e) => set("subgenre", e.target.value)} disabled={!state.genre || !SUBGENRES[state.genre]}>
              <option value="">Select subgenre...</option>
              {(SUBGENRES[state.genre || ""] || []).map((s) => <option key={s} value={s}>{s}</option>)}
            </select>
          </div>
        </div>

        <div>
          <label>Meta Language *</label>
          <select value={state.meta_language || "Spanish; Castilian"} onChange={(e) => set("meta_language", e.target.value)}>
            {META_LANGUAGES.map((l) => <option key={l} value={l}>{l}</option>)}
          </select>
        </div>

        <div>
          <label>Label Name *</label>
          <input value={state.label_name || ""} onChange={(e) => set("label_name", e.target.value)} placeholder="e.g. ADRC Producciones" />
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14 }}>
          <div>
            <label>(C) Line — Copyright *</label>
            <input value={state.c_line || `${currentYear} ${state.label_name || "AP Studios"}`} onChange={(e) => set("c_line", e.target.value)} placeholder={`${currentYear} Your Label`} />
          </div>
          <div>
            <label>(P) Line — Phonogram *</label>
            <input value={state.p_line || `${currentYear} ${state.label_name || "AP Studios"}`} onChange={(e) => set("p_line", e.target.value)} placeholder={`${currentYear} Your Label`} />
          </div>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14 }}>
          <div>
            <label>Product Version</label>
            <input value={state.product_version || ""} onChange={(e) => set("product_version", e.target.value)} placeholder="e.g. Radio Edit, Deluxe..." />
          </div>
          <div>
            <label>Internal Product Code</label>
            <input value={state.product_code || ""} onChange={(e) => set("product_code", e.target.value)} placeholder="e.g. ADRC-2026-001" />
          </div>
        </div>
      </div>

      <div className="mt-4 flex gap-2">
        <button onClick={onBack} className="btn-ghost">Atrás</button>
        <button onClick={onNext} className="btn-primary">Continuar</button>
      </div>
    </div>
  );
}
