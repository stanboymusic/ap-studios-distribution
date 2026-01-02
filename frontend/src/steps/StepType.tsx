export default function StepType({ onNext }: any) {
  return (
    <div>
      <h2 className="text-xl font-semibold">Tipo de lanzamiento</h2>
      <p className="text-gray-500 mb-4">Por ahora solo Single (Audio)</p>

      <button
        onClick={onNext}
        className="mt-4 px-4 py-2 bg-black text-white rounded"
      >
        Continuar
      </button>
    </div>
  );
}