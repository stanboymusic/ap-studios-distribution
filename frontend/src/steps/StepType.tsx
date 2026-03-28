import { useContext, useState } from "react";
import { WizardContext } from "../app/WizardProvider";

const FORMAT_CARDS = [
  { value: "Single", description: "1 track · hasta 10 min" },
  { value: "EP", description: "2-6 tracks · distribución completa" },
  { value: "Album", description: "7+ tracks · lanzamiento completo" },
];

const NoteIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden="true">
    <path d="M14 3v11.5a3.5 3.5 0 1 1-2-3.163V6l8-2v8.5a3.5 3.5 0 1 1-2-3.163V3.5L14 4.5V3Z" fill="currentColor" />
  </svg>
);

export default function StepType({ onNext }: any) {
  const { state, dispatch } = useContext(WizardContext);
  const [version, setVersion] = useState(state.ern?.version || "4.3");
  const [profile, setProfile] = useState(state.ern?.profile || "AudioAlbum");
  const [releaseType, setReleaseType] = useState(state.release?.release_type || "Single");

  const handleSubmit = () => {
    dispatch({ type: "UPDATE_ERN", payload: { version, profile } });
    dispatch({
      type: "UPDATE_RELEASE",
      payload: {
        ...(state.release || {}),
        release_type: releaseType,
      },
    });
    onNext();
  };

  return (
    <div>
      <h2 className="text-xl font-semibold">Configuración ERN</h2>
      <p style={{ color: "var(--mist-d)" }} className="mb-4">Selecciona versión y formato de lanzamiento</p>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(3, minmax(0, 1fr))", gap: 16, marginBottom: 20 }}>
        {FORMAT_CARDS.map((card) => {
          const selected = card.value === releaseType;
          return (
            <button
              type="button"
              key={card.value}
              onClick={() => setReleaseType(card.value)}
              style={{
                textAlign: "left",
                position: "relative",
                borderRadius: 12,
                padding: 24,
                border: selected ? "1px solid var(--wine-ll)" : "1px solid var(--border)",
                background: selected ? "rgba(107,26,46,0.12)" : "var(--card)",
                transform: "translateY(0)",
                transition: "all .18s ease",
                color: "var(--mist)",
              }}
              onMouseEnter={(e) => {
                if (!selected) {
                  e.currentTarget.style.borderColor = "rgba(107,26,46,0.55)";
                  e.currentTarget.style.transform = "translateY(-2px)";
                }
              }}
              onMouseLeave={(e) => {
                if (!selected) {
                  e.currentTarget.style.borderColor = "var(--border)";
                  e.currentTarget.style.transform = "translateY(0)";
                }
              }}
            >
              {selected && <div style={{ position: "absolute", top: 0, left: 0, width: "100%", height: 2, background: "linear-gradient(90deg, rgba(107,26,46,0.2), var(--wine-ll), rgba(107,26,46,0.2))" }} />}
              <div style={{ color: "var(--wine-ll)", marginBottom: 10 }}><NoteIcon /></div>
              <div style={{ fontSize: 16, fontFamily: "Cormorant Garamond, var(--font-display)", color: "var(--mist)", marginBottom: 4 }}>{card.value}</div>
              <div style={{ fontSize: 13, color: "var(--mist-d)" }}>{card.description}</div>
            </button>
          );
        })}
      </div>

      <div className="mb-4">
        <label htmlFor="ern-version">Versión ERN</label>
        <select id="ern-version" value={version} onChange={(e) => setVersion(e.target.value)} className="w-full">
          <option value="4.2">ERN 4.2</option>
          <option value="4.3">ERN 4.3</option>
        </select>
      </div>

      <div className="mb-4">
        <label htmlFor="ern-profile">Perfil</label>
        <select id="ern-profile" value={profile} onChange={(e) => setProfile(e.target.value)} className="w-full">
          <option value="AudioAlbum">Audio Album</option>
          <option value="AudioSingle">Audio Single</option>
        </select>
      </div>

      <button onClick={handleSubmit} className="btn-primary mt-4">Continuar</button>
    </div>
  );
}
