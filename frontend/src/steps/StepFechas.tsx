export default function StepFechas({ onNext, onBack }: any) {
  return (
    <div>
      <h2 className="text-xl font-semibold">[ Distribution Settings ]</h2>

      <div className="mt-4 space-y-4">
        <div className="flex items-center">
          <label className="w-32">Territories:</label>
          <span style={{ color: "var(--mist-d)" }}>Worldwide</span>
        </div>

        <div className="flex items-center">
          <label className="w-32">Release date:</label>
          <span style={{ color: "var(--mist-d)" }}>{new Date().toISOString().split('T')[0]}</span>
        </div>

        <div className="flex items-center">
          <label className="w-32">Usage:</label>
          <span style={{ color: "var(--mist-d)" }}>Streaming</span>
        </div>
      </div>

      <div className="mt-4 flex gap-2">
        <button onClick={onBack} className="btn-ghost">
          Atrás
        </button>
        <button onClick={onNext} className="btn-primary">
          Continuar
        </button>
      </div>
    </div>
  );
}
