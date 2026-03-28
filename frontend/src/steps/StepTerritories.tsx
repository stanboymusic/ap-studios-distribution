import { useState } from "react";
import { useWizard } from "../app/WizardProvider";

const TERRITORY_GROUPS = {
  "Latin America": ["Venezuela", "Colombia", "México", "Argentina", "Chile", "Perú", "Ecuador", "Bolivia", "Paraguay", "Uruguay", "Cuba", "Puerto Rico", "República Dominicana", "Guatemala", "Honduras", "El Salvador", "Nicaragua", "Costa Rica", "Panamá"],
  "North America": ["United States", "Canada"],
  Europe: ["Spain", "United Kingdom", "Germany", "France", "Italy", "Portugal"],
  Other: ["Brazil", "Japan", "South Korea", "Australia", "China", "Russia"],
};

const PRICE_TIERS = ["Front", "Mid/Front", "Mid", "Back/Mid", "Back", "Free"];

export default function StepTerritories({ onNext, onBack }: { onNext: () => void; onBack: () => void }) {
  const { state, dispatch } = useWizard();
  const set = (field: string, value: any) => dispatch({ type: "SET_FIELD", field, value });

  const [worldwideMode, setWorldwideMode] = useState(!state.excluded_territories?.length);
  const excluded = state.excluded_territories || [];

  const toggleExcluded = (country: string) => {
    const next = excluded.includes(country) ? excluded.filter((c: string) => c !== country) : [...excluded, country];
    set("excluded_territories", next);
  };

  return (
    <div style={{ maxWidth: 600, margin: "0 auto" }}>
      <div className="page-eyebrow">Step — Territories</div>
      <h2 style={{ fontFamily: "var(--font-display)", fontSize: 28, fontWeight: 300, color: "#fff", marginBottom: 6 }}>Territories & Pricing</h2>

      <div style={{ background: "var(--card)", border: "0.5px solid var(--border)", borderRadius: 12, padding: "20px 24px", marginBottom: 20 }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 16 }}>
          <div>
            <div style={{ fontSize: 15, color: "var(--mist)", fontWeight: 400 }}>Worldwide Distribution</div>
          </div>
          <div onClick={() => { const next = !worldwideMode; setWorldwideMode(next); if (next) set("excluded_territories", []); }} style={{ width: 44, height: 24, borderRadius: 12, cursor: "pointer", background: worldwideMode ? "var(--wine)" : "rgba(255,255,255,0.1)", position: "relative", transition: "background 0.2s", flexShrink: 0 }}>
            <div style={{ position: "absolute", top: 3, left: worldwideMode ? 23 : 3, width: 18, height: 18, borderRadius: "50%", background: "#fff", transition: "left 0.2s" }} />
          </div>
        </div>

        {!worldwideMode && (
          <div>
            <div style={{ fontSize: 13, color: "var(--mist-d)", marginBottom: 12 }}>Select countries to EXCLUDE from distribution:</div>
            {Object.entries(TERRITORY_GROUPS).map(([group, countries]) => (
              <div key={group} style={{ marginBottom: 14 }}>
                <div style={{ fontSize: 11, letterSpacing: "0.15em", textTransform: "uppercase", color: "var(--wine-ll)", marginBottom: 8 }}>{group}</div>
                <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
                  {countries.map((c) => (
                    <button key={c} onClick={() => toggleExcluded(c)} style={{ fontSize: 12, padding: "4px 10px", borderRadius: 20, cursor: "pointer", background: excluded.includes(c) ? "rgba(107,26,46,0.3)" : "rgba(255,255,255,0.04)", border: `0.5px solid ${excluded.includes(c) ? "rgba(168,56,90,0.6)" : "var(--border)"}`, color: excluded.includes(c) ? "var(--wine-ll)" : "var(--mist-d)" }}>{excluded.includes(c) ? "✕ " : ""}{c}</button>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <div style={{ background: "var(--card)", border: "0.5px solid var(--border)", borderRadius: 12, padding: "20px 24px", marginBottom: 20 }}>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14 }}>
          <div>
            <label>Album Price Tier</label>
            <select value={state.album_price || "Mid/Front"} onChange={(e) => set("album_price", e.target.value)}>
              {PRICE_TIERS.map((p) => <option key={p} value={p}>{p}</option>)}
            </select>
          </div>
          <div>
            <label>Track Price Tier</label>
            <select value={state.track_price || "Mid"} onChange={(e) => set("track_price", e.target.value)}>
              {PRICE_TIERS.map((p) => <option key={p} value={p}>{p}</option>)}
            </select>
          </div>
        </div>
      </div>

      <div style={{ background: "var(--card)", border: "0.5px solid var(--border)", borderRadius: 12, padding: "20px 24px" }}>
        <div style={{ display: "grid", gridTemplateColumns: "1fr auto", gap: 14 }}>
          <div>
            <label>Pre-Order Date</label>
            <input type="date" value={state.preorder_date || ""} onChange={(e) => set("preorder_date", e.target.value)} />
          </div>
          <div style={{ paddingTop: 24 }}>
            <label style={{ display: "flex", alignItems: "center", gap: 8, cursor: "pointer" }}>
              <input type="checkbox" checked={state.preorder_previewable || false} onChange={(e) => set("preorder_previewable", e.target.checked)} style={{ width: "auto", accentColor: "var(--wine)" }} />
              <span style={{ fontSize: 13, color: "var(--mist)" }}>Previewable</span>
            </label>
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
