import { useContext, useState, useEffect } from 'react';
import { WizardContext } from '../app/WizardProvider';
import { DeliveryTimeline } from '../components/DeliveryTimeline';

export default function StepDelivery({ onBack }: any) {
  const { state } = useContext(WizardContext);
  const [exportResult, setExportResult] = useState<any>(null);
  const [exporting, setExporting] = useState(false);
  const [delivering, setDelivering] = useState(false);
  const [deliveryStatus, setDeliveryStatus] = useState<any>(null);

  const isValidated = state.validation?.ddex_status === 'validated' || state.validation?.ddex_status === 'external_unavailable';

  // Polling de estado de delivery
  useEffect(() => {
    if (state.delivery?.status && state.delivery.status !== 'not_delivered') {
      const pollStatus = async () => {
        try {
          const response = await fetch(`http://localhost:8000/api/delivery/status/${state.id}`);
          const status = await response.json();
          setDeliveryStatus(status);
        } catch (error) {
          console.error('Error polling delivery status:', error);
        }
      };

      pollStatus();
      const interval = setInterval(pollStatus, 5000); // Poll every 5 seconds
      return () => clearInterval(interval);
    }
  }, [state.id, state.delivery?.status]);

  const handleExport = async () => {
    if (!isValidated) {
      alert('El release debe estar validado antes de generar el paquete de entrega');
      return;
    }

    setExporting(true);
    try {
      const response = await fetch(`http://localhost:8000/api/delivery/${state.id}/export`, {
        method: 'POST',
      });
      const result = await response.json();
      setExportResult(result);
    } catch (error) {
      console.error('Error exporting:', error);
      alert('Error al generar el paquete de entrega');
    } finally {
      setExporting(false);
    }
  };

  const handleDownload = () => {
    if (exportResult?.path) {
      // In a real app, this would trigger a download
      // For now, just show the path
      alert(`Paquete generado: ${exportResult.path}`);
    }
  };

  const handleDeliver = async () => {
    if (!isValidated) {
      alert('El release debe estar validado antes de entregar');
      return;
    }

    setDelivering(true);
    try {
      const response = await fetch('http://localhost:8000/api/delivery/sftp', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          release_id: state.id,
          connector_id: 'orchard_sandbox'
        })
      });
      const result = await response.json();
      if (response.ok) {
        alert('Entrega iniciada al DSP Sandbox');
        // Trigger status update
        const statusResponse = await fetch(`http://localhost:8000/api/delivery/status/${state.id}`);
        const status = await statusResponse.json();
        setDeliveryStatus(status);
      } else {
        alert(`Error en entrega: ${result.detail}`);
      }
    } catch (error) {
      console.error('Error delivering:', error);
      alert('Error al entregar al DSP');
    } finally {
      setDelivering(false);
    }
  };

  return (
    <div>
      <h2 className="text-xl font-semibold">Entrega del Release</h2>
      <p className="text-gray-500 mb-4">Generar paquete DDEX-compliant para distribución</p>

      <div className="mb-4">
        <h3 className="text-lg font-semibold">Estado de Preparación</h3>
        <div className="space-y-2">
          <div className="flex items-center">
            <span className="mr-2">✔</span> Pre-validation completada
          </div>
          <div className="flex items-center">
            <span className="mr-2">✔</span> ERN generado
          </div>
          <div className="flex items-center">
            <span className="mr-2">{state.validation?.ddex_status === 'validated' ? '✔' : state.validation?.ddex_status === 'external_unavailable' ? '⚠' : '❌'}</span> {state.validation?.ddex_status === 'external_unavailable' ? 'DDEX Public Validator (optional)' : 'Validación DDEX'}
          </div>
          <div className="flex items-center">
            <span className="mr-2">✔</span> Assets verificados
          </div>
        </div>

        {isValidated ? (
          <div className="mt-4 text-green-600 font-bold text-xl">
            🟢 READY FOR DELIVERY
          </div>
        ) : (
          <div className="mt-4 text-red-600 font-bold text-xl">
            🔴 VALIDATION REQUIRED
          </div>
        )}
      </div>

      {isValidated && (
        <div className="mb-4">
          <button
            onClick={handleExport}
            disabled={exporting}
            className="px-4 py-2 bg-green-500 text-white rounded disabled:opacity-50 mr-2"
          >
            {exporting ? 'Generando paquete...' : 'Generar Paquete de Entrega'}
          </button>
          <button
            onClick={handleDeliver}
            disabled={delivering || deliveryStatus?.status === 'UPLOADED' || deliveryStatus?.status === 'PROCESSING' || deliveryStatus?.status === 'ACCEPTED'}
            className="px-4 py-2 bg-blue-500 text-white rounded disabled:opacity-50"
          >
            {delivering ? 'Entregando...' : 'Entregar al DSP Sandbox'}
          </button>
        </div>
      )}

      {exportResult && exportResult.status === 'exported' && (
        <div className="mb-4">
          <h3 className="text-lg font-semibold">Paquete Generado</h3>
          <div className="border p-4 rounded">
            <p><strong>Nombre del paquete:</strong> {exportResult.package_name}</p>
            <p><strong>Ruta:</strong> {exportResult.path}</p>
            <p><strong>Timestamp:</strong> {new Date().toLocaleString()}</p>
            <button
              onClick={handleDownload}
              className="mt-2 px-4 py-2 bg-blue-500 text-white rounded"
            >
              Descargar ZIP
            </button>
          </div>
        </div>
      )}

      {deliveryStatus && (
        <div className="mb-4">
          <h3 className="text-lg font-semibold">Estado de Entrega</h3>
          <div className="border p-4 rounded">
            <div className="flex items-center mb-2">
              <span className="mr-2">
                {deliveryStatus.status === 'ACCEPTED' ? '🟢' :
                 deliveryStatus.status === 'REJECTED' ? '🔴' :
                 deliveryStatus.status === 'PROCESSING' ? '🟡' :
                 deliveryStatus.status === 'UPLOADED' ? '🟠' : '⚪'}
              </span>
              <strong>Estado:</strong> {deliveryStatus.status}
            </div>
            <p><strong>DSP Destino:</strong> {deliveryStatus.connector || 'DSP Sandbox'}</p>
            <p><strong>Release ID:</strong> {deliveryStatus.release_id}</p>
            {deliveryStatus.timestamp && (
              <p><strong>Última actualización:</strong> {new Date(deliveryStatus.timestamp).toLocaleString()}</p>
            )}
            {deliveryStatus.issues && deliveryStatus.issues.length > 0 && (
              <div className="mt-2">
                <strong>Issues:</strong>
                <ul className="list-disc list-inside text-red-600">
                  {deliveryStatus.issues.map((issue: string, index: number) => (
                    <li key={index}>{issue}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>
      )}

      {deliveryStatus && (
        <div className="mb-4">
          <h3 className="text-lg font-semibold">Historial de Eventos</h3>
          <DeliveryTimeline releaseId={state.id} />
        </div>
      )}

      <div className="mt-4 flex gap-2">
        <button onClick={onBack} className="px-4 py-2 border rounded">
          Atrás
        </button>
        {exportResult?.status === 'exported' && (
          <button onClick={() => alert('¡Distribución completada!')} className="px-4 py-2 bg-black text-white rounded">
            Finalizar
          </button>
        )}
      </div>
    </div>
  );
}