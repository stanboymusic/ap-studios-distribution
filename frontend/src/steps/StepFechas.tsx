export default function StepFechas({ onNext, onBack }: any) {
  return (
    <div>
      <h2 className="text-xl font-semibold">[ Distribution Settings ]</h2>

      <div className="mt-4 space-y-4">
        <div className="flex items-center">
          <label className="w-32">Territories:</label>
          <span className="text-gray-700">Worldwide</span>
        </div>

        <div className="flex items-center">
          <label className="w-32">Release date:</label>
          <span className="text-gray-700">{new Date().toISOString().split('T')[0]}</span>
        </div>

        <div className="flex items-center">
          <label className="w-32">Usage:</label>
          <span className="text-gray-700">Streaming</span>
        </div>
      </div>

      <div className="mt-4 flex gap-2">
        <button onClick={onBack} className="px-4 py-2 border rounded">
          Atrás
        </button>
        <button onClick={onNext} className="px-4 py-2 bg-black text-white rounded">
          Continuar
        </button>
      </div>
    </div>
  );
}