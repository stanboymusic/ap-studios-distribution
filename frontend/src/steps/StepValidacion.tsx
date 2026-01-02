import { useContext, useState } from 'react';
import { WizardContext } from '../app/WizardProvider';

export default function StepValidacion({ onNext, onBack }: any) {
  const { state } = useContext(WizardContext);
  const [validationResult, setValidationResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [exportResult, setExportResult] = useState<any>(null);
  const [exporting, setExporting] = useState(false);

  const handleValidate = async () => {
    setLoading(true);
    try {
      const response = await fetch(`http://127.0.0.1:8000/validation/${state.id}/ddex`, {
        method: 'POST',
      });
      const result = await response.json();
      setValidationResult(result);
    } catch (error) {
      console.error('Error validating:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleExport = async () => {
    setExporting(true);
    try {
      const response = await fetch(`http://127.0.0.1:8000/delivery/${state.id}/export`, {
        method: 'POST',
      });
      const result = await response.json();
      setExportResult(result);
    } catch (error) {
      console.error('Error exporting:', error);
    } finally {
      setExporting(false);
    }
  };

  return (
    <div>
      <h2 className="text-xl font-semibold">Validación</h2>
      <p className="text-gray-500 mb-4">Validación final del lanzamiento con DDEX Workbench</p>

      <div className="mb-4">
        <button
          onClick={handleValidate}
          disabled={loading}
          className="px-4 py-2 bg-blue-500 text-white rounded disabled:opacity-50"
        >
          {loading ? 'Validando...' : 'Validar con DDEX'}
        </button>
      </div>

      {validationResult && (
        <div className="mb-4">
          <h3 className="text-lg font-semibold">Estado de Validación</h3>
          <div className="mb-4">
            {validationResult.status === 'validated' ? (
              <div className="text-green-600 font-bold text-xl">🟢 VALID</div>
            ) : (
              <div className="text-red-600 font-bold text-xl">🔴 INVALID</div>
            )}
          </div>
          <div className="space-y-2">
            <div className="flex items-center">
              <span className="mr-2">✔</span> Pre-validation
            </div>
            <div className="flex items-center">
              <span className="mr-2">✔</span> ERN Generated
            </div>
            <div className="flex items-center">
              <span className="mr-2">{validationResult.status === 'validated' ? '✔' : '❌'}</span> DDEX Validation
            </div>
          </div>

          {validationResult.ddex_errors && validationResult.ddex_errors.length > 0 && (
            <div className="mt-4">
              <h4 className="font-semibold text-red-600">Errores encontrados ({validationResult.ddex_errors.length}):</h4>
              {(() => {
                const groupedErrors = validationResult.ddex_errors.reduce((acc: any, error: any) => {
                  const section = error.section || 'Otros';
                  if (!acc[section]) acc[section] = [];
                  acc[section].push(error);
                  return acc;
                }, {});

                return Object.entries(groupedErrors).map(([section, errors]: [string, any]) => (
                  <div key={section} className="mt-2">
                    <h5 className="font-medium text-red-700">{section}</h5>
                    <ul className="list-disc list-inside ml-4">
                      {errors.map((error: any, index: number) => (
                        <li key={index} className="text-red-600 text-sm">
                          {error.message} <span className="text-gray-500">({error.rule})</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                ));
              })()}
            </div>
          )}

          {validationResult.status === 'validated' && (
            <div className="mt-4 text-green-600 font-semibold">
              ✔ Release listo para entrega
            </div>
          )}
        </div>
      )}

      {validationResult?.status === 'validated' && (
        <div className="mt-4">
          <button
            onClick={handleExport}
            disabled={exporting}
            className="px-4 py-2 bg-green-500 text-white rounded disabled:opacity-50"
          >
            {exporting ? 'Exportando...' : 'Exportar Release'}
          </button>

          {exportResult && (
            <div className="mt-2 text-green-600">
              ✔ Bundle exportado: {exportResult.path}
            </div>
          )}
        </div>
      )}

      <div className="mt-4 flex gap-2">
        <button onClick={onBack} className="px-4 py-2 border rounded">
          Atrás
        </button>
        {validationResult?.status === 'validated' && onNext && (
          <button onClick={onNext} className="px-4 py-2 bg-black text-white rounded">
            Continuar a Entrega
          </button>
        )}
      </div>
    </div>
  );
}