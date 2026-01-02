import { useState } from "react";
import StepType from "../steps/StepType";
import StepArtist from "../steps/StepArtist";
import StepRelease from "../steps/StepRelease";
import StepTracks from "../steps/StepTracks";
import StepArtwork from "../steps/StepArtwork";
import StepFechas from "../steps/StepFechas";
import StepPreview from "../steps/StepPreview";
import StepValidacion from "../steps/StepValidacion";
import StepDelivery from "../steps/StepDelivery";

const steps = ["Tipo", "Artista", "Release", "Tracks", "Artwork", "Fechas", "Preview", "Validación", "Entrega"];

export default function ReleaseWizard() {
  const [current, setCurrent] = useState(0);

  return (
    <div className="max-w-4xl mx-auto p-6">
      <h1 className="text-2xl font-bold mb-4">Nuevo Lanzamiento</h1>
      <div className="mb-6">
        <div className="flex justify-between">
          {steps.map((step, index) => (
            <div
              key={index}
              className={`flex-1 text-center py-2 ${
                index <= current ? "bg-black text-white" : "bg-gray-200"
              }`}
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
      {current === 4 && <StepArtwork onNext={() => setCurrent(5)} onBack={() => setCurrent(3)} />}
      {current === 5 && <StepFechas onNext={() => setCurrent(6)} onBack={() => setCurrent(4)} />}
      {current === 6 && <StepPreview onNext={() => setCurrent(7)} onBack={() => setCurrent(5)} />}
      {current === 7 && <StepValidacion onNext={() => setCurrent(8)} onBack={() => setCurrent(6)} />}
      {current === 8 && <StepDelivery onBack={() => setCurrent(7)} />}
    </div>
  );
}