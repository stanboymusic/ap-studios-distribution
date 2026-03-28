import { useMemo, useState } from "react";
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
import StepCredits from "../steps/StepCredits";
import StepGenre from "../steps/StepGenre";
import StepTerritories from "../steps/StepTerritories";
import StepPublishing from "../steps/StepPublishing";
import { useWizard } from "../app/WizardProvider";

const STEPS = [
  { id: "type", label: "Format" },
  { id: "artist", label: "Artist" },
  { id: "credits", label: "Credits" },
  { id: "release", label: "Details" },
  { id: "genre", label: "Genre" },
  { id: "tracks", label: "Tracks" },
  { id: "rights", label: "Rights" },
  { id: "artwork", label: "Artwork" },
  { id: "fechas", label: "Dates" },
  { id: "territories", label: "Territories" },
  { id: "publishing", label: "Publishing" },
  { id: "preview", label: "Preview" },
  { id: "validation", label: "Validate" },
  { id: "delivery", label: "Deliver" },
];

export default function ReleaseWizard({ onFinish }: { onFinish?: () => void }) {
  const [current, setCurrent] = useState(0);
  const { showDraftBanner, continueDraft, startFresh, savedDraftMeta } = useWizard();

  const currentStep = STEPS[current];
  const progress = ((current + 1) / STEPS.length) * 100;

  const content = useMemo(() => {
    if (current === 0) return <StepType onNext={() => setCurrent(1)} />;
    if (current === 1) return <StepArtist onNext={() => setCurrent(2)} onBack={() => setCurrent(0)} />;
    if (current === 2) return <StepCredits onNext={() => setCurrent(3)} onBack={() => setCurrent(1)} />;
    if (current === 3) return <StepRelease onNext={() => setCurrent(4)} onBack={() => setCurrent(2)} />;
    if (current === 4) return <StepGenre onNext={() => setCurrent(5)} onBack={() => setCurrent(3)} />;
    if (current === 5) return <StepTracks onNext={() => setCurrent(6)} onBack={() => setCurrent(4)} />;
    if (current === 6) return <StepRights onNext={() => setCurrent(7)} onBack={() => setCurrent(5)} />;
    if (current === 7) return <StepArtwork onNext={() => setCurrent(8)} onBack={() => setCurrent(6)} />;
    if (current === 8) return <StepFechas onNext={() => setCurrent(9)} onBack={() => setCurrent(7)} />;
    if (current === 9) return <StepTerritories onNext={() => setCurrent(10)} onBack={() => setCurrent(8)} />;
    if (current === 10) return <StepPublishing onNext={() => setCurrent(11)} onBack={() => setCurrent(9)} />;
    if (current === 11) return <StepPreview onNext={() => setCurrent(12)} onBack={() => setCurrent(10)} />;
    if (current === 12) return <StepValidacion onNext={() => setCurrent(13)} onBack={() => setCurrent(11)} />;
    if (current === 13) return <StepDelivery onBack={() => setCurrent(12)} onFinish={onFinish} />;
    return null;
  }, [current, onFinish]);

  return (
    <div className="max-w-5xl mx-auto p-6">
      <div className="flex justify-between items-center mb-4">
        <h1 style={{ fontSize: 22, fontFamily: "var(--font-display)", color: "#fff" }}>Nuevo Lanzamiento</h1>
        <button onClick={onFinish} className="btn-ghost text-sm">Cancelar</button>
      </div>

      {showDraftBanner && (
        <div style={{ background: "rgba(201,169,110,0.08)", border: "0.5px solid rgba(201,169,110,0.25)", borderRadius: 10, padding: "14px 18px", color: "var(--gold-l)", marginBottom: 14 }}>
          <div style={{ marginBottom: 10 }}>
            You have an unsaved draft{savedDraftMeta ? ` from ${new Date(savedDraftMeta).toLocaleString()}` : ""}. Continue?
          </div>
          <div className="flex gap-2">
            <button className="btn-primary" onClick={continueDraft}>Continue draft</button>
            <button className="btn-ghost" onClick={startFresh}>Start fresh</button>
          </div>
        </div>
      )}

      <div className="mb-6">
        <div className="md:hidden" style={{ color: "var(--mist)", fontSize: 13, marginBottom: 8 }}>
          Step {current + 1} de {STEPS.length} · {currentStep.label}
        </div>
        <div style={{ height: 8, background: "rgba(107,26,46,0.15)", borderRadius: 9999, overflow: "hidden", marginBottom: 16 }}>
          <div style={{ width: `${progress}%`, height: "100%", background: "linear-gradient(90deg, var(--wine), var(--wine-ll))", transition: "width .25s" }} />
        </div>

        <div className="hidden md:flex justify-between items-start gap-2">
          {STEPS.map((step, index) => {
            const done = index < current;
            const active = index === current;
            return (
              <div key={step.id} style={{ flex: 1, textAlign: "center" }}>
                <div style={{ margin: "0 auto 6px", width: active ? 16 : 10, height: active ? 16 : 10, borderRadius: "999px", background: done ? "var(--success)" : active ? "var(--wine)" : "var(--mist-d)", boxShadow: active ? "0 0 12px rgba(107,26,46,0.85)" : "none", display: "grid", placeItems: "center", fontSize: 10, color: "#0b1210" }}>{done ? "✓" : ""}</div>
                <div style={{ fontSize: 11, color: active ? "var(--mist)" : "var(--mist-d)" }}>{step.label}</div>
              </div>
            );
          })}
        </div>
      </div>

      {content}
    </div>
  );
}
