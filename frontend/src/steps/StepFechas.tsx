import { useWizard } from "../app/WizardProvider";

export default function StepFechas({ onNext, onBack }: any) {
  const { state, dispatch } = useWizard();
  const releaseDate = state.release?.original_release_date || new Date().toISOString().split('T')[0];

  return (
    <div>
      <h2 className="text-xl font-semibold">[ Distribution Settings ]</h2>

      <div className="mt-4 space-y-4">
        <div className="flex items-center">
          <label className="w-40">Release date:</label>
          <span style={{ color: "var(--mist-d)" }}>{releaseDate}</span>
        </div>

        <div className="flex items-center gap-4">
          <label className="w-40">Sale date:</label>
          <input
            type="date"
            value={state.sale_date || releaseDate}
            onChange={(e) => dispatch({ type: "SET_FIELD", field: "sale_date", value: e.target.value })}
          />
        </div>
      </div>

      <div className="mt-4 flex gap-2">
        <button onClick={onBack} className="btn-ghost">Atrás</button>
        <button onClick={onNext} className="btn-primary">Continuar</button>
      </div>
    </div>
  );
}
