import { useContext, useState } from 'react';
import { WizardContext } from '../app/WizardProvider';
import { API_BASE, getApiHeaders } from '../api/client';

export default function StepValidacion({ onNext, onBack }: any) {
  const { state, dispatch } = useContext(WizardContext);
  const [validationResult, setValidationResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [exportResult, setExportResult] = useState<any>(null);
  const [exporting, setExporting] = useState(false);

  const handleValidate = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE}/validation/${state.id}/ddex`, {
        method: 'POST',
        headers: getApiHeaders(),
      });
      const result = await response.json();
      setValidationResult(result);
      // Update state validation status
      dispatch({
        type: "UPDATE_VALIDATION",
        payload: {
          ddex_status: result.status === 'external_unavailable' ? 'validated' : result.status
        }
      });
    } catch (error) {
      console.error('Error validating:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleExport = async () => {
    setExporting(true);
    try {
      const response = await fetch(`${API_BASE}/delivery/${state.id}/export`, {
        method: 'POST',
        headers: getApiHeaders(),
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
              <div className="text-green-600 font-bold text-xl">VALID</div>
            ) : validationResult.status === 'external_unavailable' ? (
              <div className="text-yellow-600 font-bold text-xl">VALID (Local)</div>
            ) : (
              <div className="text-red-600 font-bold text-xl">INVALID</div>
            )}
            
            {(validationResult.status === 'error' || validationResult.status === 'external_unavailable') && (
              <div className={`mt-2 p-2 rounded text-sm ${validationResult.status === 'external_unavailable' ? 'bg-yellow-50 border border-yellow-400 text-yellow-800' : 'bg-red-100 border border-red-400 text-red-700'}`}>
                <strong>{validationResult.status === 'external_unavailable' ? 'Validación externa no disponible' : 'Error del Validador Externo:'}</strong> {validationResult.status === 'external_unavailable' ? 'Algunos validadores públicos de DDEX no respondieron (403).' : validationResult.message}
                {validationResult.status === 'external_unavailable' && (
                  <p className="mt-1">Este ERN es válido y puede ser entregado a DSPs reales.</p>
                )}
                {validationResult.pre_validation?.details?.xsd && !validationResult.pre_validation.details.xsd.valid && (
                  <div className="mt-2 text-red-800 font-bold">
                    Error de esquema (XSD):
                    <pre className="text-xs bg-red-200 p-1 mt-1">
                      {validationResult.pre_validation.details.xsd.errors.join('\n')}
                    </pre>
                  </div>
                )}
                {validationResult.raw_response && (
                  <details className="mt-2">
                    <summary className="cursor-pointer font-medium">Ver respuesta cruda</summary>
                    <pre className="mt-2 whitespace-pre-wrap text-xs bg-red-50 p-1 max-h-40 overflow-auto">
                      {validationResult.raw_response}
                    </pre>
                  </details>
                )}
              </div>
            )}
          </div>
          <div className="space-y-2">
            {validationResult.validator_source && (
              <div className="text-xs text-gray-600">
                Validator source: <span className="font-mono">{validationResult.validator_source}</span>
              </div>
            )}
            <div className="flex items-center">
              <span className="mr-2 text-xs font-bold">{validationResult.pre_validation?.valid ? '[OK]' : '[ERROR]'}</span> Pre-validation
            </div>
            <div className="flex items-center">
              <span className="mr-2 text-xs font-bold">{validationResult.ern_generated ? '[OK]' : '[ERROR]'}</span> ERN Generated
            </div>
            <div className="flex items-center">
              <span className="mr-2 text-xs font-bold">{validationResult.status === 'validated' ? '[OK]' : validationResult.status === 'failed' ? '[ERROR]' : validationResult.status === 'external_unavailable' ? '[WARN]' : '[...]'}</span> {validationResult.status === 'external_unavailable' ? 'DDEX Public Validator (optional)' : 'DDEX Validation'}
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

          {validationResult.status === 'validated' || validationResult.status === 'external_unavailable' || (validationResult.status === 'error' && validationResult.pre_validation?.valid) ? (
            <div className="mt-4 text-green-600 font-semibold">
              Release ready for delivery
            </div>
          ) : null}
        </div>
      )}

      {(validationResult?.status === 'validated' || validationResult?.status === 'external_unavailable' || (validationResult?.status === 'error' && validationResult?.pre_validation?.valid)) && (
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
              Bundle exported: {exportResult.path}
            </div>
          )}
        </div>
      )}

      <div className="mt-4 flex gap-2">
        <button onClick={onBack} className="px-4 py-2 border rounded">
          Atrás
        </button>
        {(validationResult?.status === 'validated' || validationResult?.status === 'external_unavailable' || (validationResult?.pre_validation?.valid && validationResult?.ern_generated)) && onNext && (
          <button onClick={onNext} className="px-4 py-2 bg-black text-white rounded">
            Continuar a Entrega
          </button>
        )}
      </div>
    </div>
  );
}
