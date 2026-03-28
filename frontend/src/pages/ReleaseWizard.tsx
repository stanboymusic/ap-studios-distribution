import { useState } from "react";
import StepType from "../steps/StepType";
import StepArtist from "../steps/StepArtist";
import StepRelease from "../steps/StepRelease";
import StepTracks from "../steps/StepTracks";
import StepRights from "../steps/StepRights";
import StepArtwork from "../steps/StepArtwork";
import StepFechas from "../steps/StepFechas";
import StepPreview from "../steps/StepPreview";
import StepValidacion from "../steps/StepValidacion";
import StepDelivery from "../steps/StepDelivery";
import { useAuth } from "../app/auth";

export default function ReleaseWizard({ onFinish }: { onFinish?: () => void }) {
  const { user } = useAuth();
  const isAdmin = user?.role === "admin";
  const steps = isAdmin
    ? ["Tipo", "Artista", "Release", "Tracks", "Derechos", "Artwork", "Fechas", "Preview", "Validación", "Entrega"]
    : ["Tipo", "Artista", "Release", "Tracks", "Derechos", "Artwork", "Fechas", "Preview"];
  const [current, setCurrent] = useState(0);

  return (
    <div className="max-w-4xl mx-auto p-6">
      <div className="flex justify-between items-center mb-4">
        <h1 style={{ fontSize: 22, fontFamily: "var(--font-display)", color: "#fff" }}>Nuevo Lanzamiento</h1>
        <button 
          onClick={onFinish}
          className="btn-ghost text-sm"
        >
          Cancelar
        </button>
      </div>
      
      <div className="mb-6">
        <div className="flex justify-between">
          {steps.map((step, index) => (
            <div
              key={index}
              className="flex-1 text-center py-3 text-[14px]"
              style={{
                background: index < current ? "rgba(93,191,138,0.15)" : index === current ? "var(--wine)" : "rgba(107,26,46,0.15)",
                color: index < current ? "var(--success)" : index === current ? "#fff" : "var(--mist-d)",
                borderRight: index < steps.length - 1 ? "0.5px solid var(--border)" : "none",
              }}
            >
              {step}
            </div>
          ))}
        </div>
      </div>

      {current === 0 && <StepType onNext={() => setCurrent(1)} />}
      {current === 1 && <StepArtist onNext={() => setCurrent(2)} onBack={() => setCurrent(0)} />}
      {current === 2 && <StepRelease onNext={() => setCurrent(3)} onBack={() => setCurrent(1)} />}
      {current === 3 && <StepTracks onNext={() => setCurrent(4)} onBack={() => setCurrent(2)} />}
      {current === 4 && <StepRights onNext={() => setCurrent(5)} onBack={() => setCurrent(3)} />}
      {current === 5 && <StepArtwork onNext={() => setCurrent(6)} onBack={() => setCurrent(4)} />}
      {current === 6 && <StepFechas onNext={() => setCurrent(7)} onBack={() => setCurrent(5)} />}
      {current === 7 && (
        <StepPreview
          onNext={() => {
            if (isAdmin) setCurrent(8);
            else onFinish?.();
          }}
          onBack={() => setCurrent(6)}
        />
      )}
      {isAdmin && current === 8 && <StepValidacion onNext={() => setCurrent(9)} onBack={() => setCurrent(7)} />}
      {isAdmin && current === 9 && <StepDelivery onBack={() => setCurrent(8)} />}
    </div>
  );
}
