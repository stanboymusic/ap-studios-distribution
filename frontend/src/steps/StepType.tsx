import { useContext, useState } from "react";
import { WizardContext } from "../app/WizardProvider";

const FORMAT_CARDS = [
  { value: "Single", description: "1 track · hasta 10 min" },
  { value: "EP", description: "2-6 tracks · distribución completa" },
  { value: "Album", description: "7+ tracks · lanzamiento completo" },
];

export default function StepType({ onNext }: any) {
  const { state, dispatch } = useContext(WizardContext);
  const [version, setVersion] = useState(state.ern?.version || "4.3");
  const [profile, setProfile] = useState(state.ern?.profile || "AudioAlbum");
  const [releaseType, setReleaseType] = useState(state.release?.release_type || "Single");

  const handleSubmit = () => {
    dispatch({ type: "UPDATE_ERN", payload: { version, profile } });
    dispatch({ type: "UPDATE_RELEASE", payload: { ...(state.release || {}), release_type: releaseType } });
    onNext();
  };

  return (
    <div>
      <h2 className="text-xl font-semibold">Configuración ERN</h2>
      <p style={{ color: "var(--mist-d)" }} className="mb-4">Selecciona versión y formato de lanzamiento</p>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(3, minmax(0, 1fr))", gap: 16, marginBottom: 20 }}>
        {FORMAT_CARDS.map(card => {
          const selected = card.value === releaseType;
          return (
            <button
              key={card.value}
              type="button"
              onClick={() => setReleaseType(card.value)}
              style={{
                borderRadius: 12, padding: 20, textAlign: "left",
                border: selected ? "1px solid var(--wine-ll)" : "1px solid var(--border)",
                background: selected ? "rgba(107,26,46,0.12)" : "var(--card)"
              }}
            >
              <div style={{ fontSize: 16, color: "var(--mist)" }}>{card.value}</div>
              <div style={{ fontSize: 13, color: "var(--mist-d)" }}>{card.description}</div>
            </button>
          );
        })}
      </div>

      <label>Versión ERN</label>
      <select value={version} onChange={e => setVersion(e.target.value)} className="w-full">
        <option value="4.2">ERN 4.2</option>
        <option value="4.3">ERN 4.3</option>
      </select>

      <label>Perfil</label>
      <select value={profile} onChange={e => setProfile(e.target.value)} className="w-full">
        <option value="AudioAlbum">Audio Album</option>
        <option value="AudioSingle">Audio Single</option>
      </select>

      <button onClick={handleSubmit} className="btn-primary mt-4">Continuar</button>
    </div>
  );
}
