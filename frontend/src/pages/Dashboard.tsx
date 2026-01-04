import { useState, useEffect } from 'react';
import { apiFetch } from '../api/client';
import { DeliveryOverview, DeliveryEvent } from '../api/schema';

export default function Dashboard() {
  const [overview, setOverview] = useState<DeliveryOverview[]>([]);
  const [selectedRelease, setSelectedRelease] = useState<string | null>(null);
  const [events, setEvents] = useState<DeliveryEvent[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadOverview();
  }, []);

  const loadOverview = async () => {
    try {
      const data = await apiFetch<DeliveryOverview[]>('/delivery/overview');
      setOverview(data);
    } catch (error) {
      console.error('Error loading overview:', error);
      setOverview([]);
    } finally {
      setLoading(false);
    }
  };

  const loadEvents = async (releaseId: string) => {
    try {
      const data = await apiFetch<DeliveryEvent[]>(`/delivery/events/${releaseId}`);
      setEvents(data);
    } catch (error) {
      console.error('Error loading events:', error);
      setEvents([]);
    }
  };

  const handleViewDetails = (releaseId: string) => {
    setSelectedRelease(releaseId);
    loadEvents(releaseId);
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'ACCEPTED': return 'text-green-600 bg-green-100';
      case 'REJECTED': return 'text-red-600 bg-red-100';
      case 'PROCESSING': return 'text-yellow-600 bg-yellow-100';
      case 'UPLOADED': return 'text-blue-600 bg-blue-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'ACCEPTED': return '🟢';
      case 'REJECTED': return '🔴';
      case 'PROCESSING': return '🟡';
      case 'UPLOADED': return '🟠';
      default: return '⚪';
    }
  };

  if (loading) {
    return (
      <div className="p-6">
        <h1 className="text-2xl font-bold mb-6">Dashboard de Entregas</h1>
        <div className="text-center">Cargando...</div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-6">Dashboard de Entregas</h1>

      {!selectedRelease ? (
        // Vista general
        <div>
          <h2 className="text-xl font-semibold mb-4">Entregas Recientes</h2>
          {overview.length === 0 ? (
            <p className="text-gray-500">No hay entregas para mostrar</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full bg-white border border-gray-300">
                <thead>
                  <tr className="bg-gray-50">
                    <th className="px-4 py-2 border-b text-left">Release</th>
                    <th className="px-4 py-2 border-b text-left">DSP</th>
                    <th className="px-4 py-2 border-b text-left">Estado</th>
                    <th className="px-4 py-2 border-b text-left">Última Actualización</th>
                    <th className="px-4 py-2 border-b text-left">Acción</th>
                  </tr>
                </thead>
                <tbody>
                  {overview.map((item) => (
                    <tr key={item.release_id} className="hover:bg-gray-50">
                      <td className="px-4 py-2 border-b">{item.title}</td>
                      <td className="px-4 py-2 border-b">{item.dsp}</td>
                      <td className="px-4 py-2 border-b">
                        <span className={`px-2 py-1 rounded-full text-sm font-medium ${getStatusColor(item.status)}`}>
                          {getStatusIcon(item.status)} {item.status}
                        </span>
                      </td>
                      <td className="px-4 py-2 border-b">
                        {item.last_event ? new Date(item.last_event).toLocaleString() : 'N/A'}
                      </td>
                      <td className="px-4 py-2 border-b">
                        <button
                          onClick={() => handleViewDetails(item.release_id)}
                          className="px-3 py-1 bg-blue-500 text-white rounded hover:bg-blue-600"
                        >
                          Ver Detalles
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      ) : (
        // Vista detalle
        <div>
          <div className="mb-4">
            <button
              onClick={() => setSelectedRelease(null)}
              className="px-4 py-2 bg-gray-500 text-white rounded hover:bg-gray-600"
            >
              ← Volver al Dashboard
            </button>
          </div>

          <h2 className="text-xl font-semibold mb-4">Timeline de Eventos</h2>

          {events.length === 0 ? (
            <p className="text-gray-500">No hay eventos para mostrar</p>
          ) : (
            <div className="space-y-4">
              {events.map((event, index) => (
                <div key={index} className="border-l-4 border-blue-500 pl-4 py-2">
                  <div className="flex items-center mb-1">
                    <span className="font-medium text-blue-600">{event.event_type}</span>
                    <span className="ml-2 text-sm text-gray-500">
                      {new Date(event.created_at).toLocaleString()}
                    </span>
                  </div>
                  <p className="text-gray-700">{event.message}</p>
                </div>
              ))}
            </div>
          )}

          {/* Mostrar issues si hay */}
          {events.some(e => e.event_type === 'REJECTED') && (
            <div className="mt-6 p-4 bg-red-50 border border-red-200 rounded">
              <h3 className="text-lg font-semibold text-red-800 mb-2">Issues Encontrados</h3>
              <ul className="list-disc list-inside text-red-700">
                {events
                  .filter(e => e.event_type === 'REJECTED')
                  .map((event, index) => (
                    <li key={index}>{event.message}</li>
                  ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}