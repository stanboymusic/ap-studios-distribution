import { useWizard } from "../app/WizardProvider";

export default function StepFechas({ onNext, onBack }: any) {
  const { state, dispatch } = useWizard();
  const releaseDate = state.release?.original_release_date || new Date().toISOString().split("T")[0];

  return (
    <div>
      <h2 className="text-xl font-semibold">[ Distribution Settings ]</h2>
      <label>Release date</label>
      <div>{releaseDate}</div>

      <label>Sale date</label>
      <input
        type="date"
        value={state.sale_date || releaseDate}
        onChange={e => dispatch({ type: "SET_FIELD", field: "sale_date", value: e.target.value })}
      />

      <div className="mt-4 flex gap-2">
        <button onClick={onBack} className="btn-ghost">Atrás</button>
        <button onClick={onNext} className="btn-primary">Continuar</button>
      </div>
    </div>
  );
}
