import { useContext, useState, useEffect } from 'react';
import { WizardContext } from '../app/WizardProvider';
import { buildErnPayload } from '../utils/ernPayload';
import { API_BASE, getApiHeaders } from '../api/client';

interface Props {
  onNext: () => void;
  onBack: () => void;
}

export default function StepPreview({ onNext, onBack }: Props) {
  const { state } = useContext(WizardContext);
  const [previewData, setPreviewData] = useState<any>(null);
  const [xml, setXml] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string>('');

  useEffect(() => {
    loadPreview();
  }, [state]);

  const loadPreview = async () => {
    setLoading(true);
    setError('');
    try {
      const payload = {
        ...buildErnPayload(state),
        release_id: state.id,
        tenant_id: localStorage.getItem("tenantId") || "default",
      };
      console.log('DEBUG: ERN Payload being sent:', payload);
      const response = await fetch(`${API_BASE}/validation/preview-ern`, {
        method: 'POST',
        headers: getApiHeaders(),
        body: JSON.stringify(payload)
      });
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || 'Error fetching preview');
      }
      setPreviewData(data);

      // Also generate XML
      const xmlResponse = await fetch(`${API_BASE}/validation/generate-ern`, {
        method: 'POST',
        headers: getApiHeaders(),
        body: JSON.stringify(payload)
      });
      const xmlData = await xmlResponse.json();
      if (!xmlResponse.ok) {
        throw new Error(xmlData.detail || 'Error generating XML');
      }
      setXml(xmlData.xml);
    } catch (error) {
      console.error('Error loading preview:', error);
      setError(error instanceof Error ? error.message : String(error));
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div>Loading preview...</div>;
  }

  if (error) {
    return <div>Error: {error}</div>;
  }

  return (
    <div className="space-y-6">
      <h2 className="text-xl font-semibold">Preview & Validate</h2>
      <p style={{ color: "var(--mist-d)" }}>Review the ERN that will be generated</p>

      {(!state.tracks || state.tracks.length === 0) && (
        <div className="p-4 rounded" style={{ background: "rgba(168,56,90,0.1)", border: "0.5px solid rgba(168,56,90,0.3)", color: "var(--wine-ll)" }}>
          <strong>Atención:</strong> No se han detectado tracks en este lanzamiento. 
          Vuelve al paso de "Tracks" para añadir al menos uno.
        </div>
      )}

      {previewData && (
        <>
          {/* Summary Cards */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div style={{ background: "var(--card)", border: "0.5px solid var(--border)", borderRadius: 8, padding: 16 }}>
              <div className="text-sm" style={{ color: "var(--mist-d)" }}>Profile</div>
              <div className="font-semibold">{previewData.summary.profile}</div>
            </div>
            <div style={{ background: "var(--card)", border: "0.5px solid var(--border)", borderRadius: 8, padding: 16 }}>
              <div className="text-sm" style={{ color: "var(--mist-d)" }}>ERN Version</div>
              <div className="font-semibold">{previewData.summary.ern_version}</div>
            </div>
            <div style={{ background: "var(--card)", border: "0.5px solid var(--border)", borderRadius: 8, padding: 16 }}>
              <div className="text-sm" style={{ color: "var(--mist-d)" }}>Releases</div>
              <div className="font-semibold">{previewData.summary.releases_count}</div>
            </div>
            <div style={{ background: "var(--card)", border: "0.5px solid var(--border)", borderRadius: 8, padding: 16 }}>
              <div className="text-sm" style={{ color: "var(--mist-d)" }}>Tracks</div>
              <div className="font-semibold">{previewData.summary.tracks_count}</div>
            </div>
          </div>

          {/* Release Tree */}
          {previewData.release && (
            <div className="border rounded p-4">
              <h3 className="font-semibold mb-2">Release</h3>
              <div className="ml-4 space-y-1">
                <div>Title: {previewData.release.title}</div>
                <div>Artist: {previewData.release.artist}</div>
                <div>UPC: {previewData.release.upc}</div>
                <div>Release Date: {previewData.release.release_date}</div>
                <div>
                  <div className="font-medium">Tracks:</div>
                  <div className="ml-4 space-y-1">
                    {previewData.release.tracks.map((track: any, index: number) => (
                      <div key={index}>
                        {index + 1}. {track.title} ({track.isrc}) - {track.duration}s
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Deals Table */}
          <div className="border rounded p-4">
            <h3 className="font-semibold mb-2">Deals & Territories</h3>
            <table className="w-full">
              <thead>
                <tr className="border-b">
                  <th className="text-left">Model</th>
                  <th className="text-left">Use Type</th>
                  <th className="text-left">Start Date</th>
                  <th className="text-left">End Date</th>
                  <th className="text-left">Territories</th>
                </tr>
              </thead>
              <tbody>
                {previewData.deals.map((deal: any, index: number) => (
                  <tr key={index} className="border-b">
                    <td>{deal.model}</td>
                    <td>{deal.use_type}</td>
                    <td>{deal.start_date}</td>
                    <td>{deal.end_date || '∞'}</td>
                    <td>{deal.territories.join(', ')}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Assets */}
          <div className="border rounded p-4">
            <h3 className="font-semibold mb-2">Assets</h3>
            <div className="space-y-2">
              {previewData.assets.map((asset: any, index: number) => (
                <div key={index} className="flex items-center space-x-2">
                  <span className="text-green-600 font-bold">[OK]</span>
                  <span>{asset.type.toUpperCase()}: {asset.filename}</span>
                  {asset.format && <span>({asset.format})</span>}
                </div>
              ))}
            </div>
          </div>

          {/* Message Header */}
          <div className="border rounded p-4">
            <h3 className="font-semibold mb-2">Message Header</h3>
            <div className="space-y-1">
              <div>Message ID: {previewData.header.message_id}</div>
              <div>Sender: {previewData.header.sender}</div>
              <div>Recipient: {previewData.header.recipient}</div>
              <div>Created: {previewData.header.created_at}</div>
              <div>Language: {previewData.header.language}</div>
            </div>
          </div>

          {/* XML Viewer */}
          <div className="border rounded p-4">
            <h3 className="font-semibold mb-2">XML Preview</h3>
            <pre style={{ background: "rgba(255,255,255,0.03)", border: "0.5px solid var(--border)", borderRadius: 8, padding: 8, fontSize: 13, color: "var(--mist-d)" }} className="overflow-auto max-h-64">
              {xml.substring(0, 1000)}...
            </pre>
            <button
              className="btn-ghost mt-2"
              onClick={() => navigator.clipboard.writeText(xml)}
            >
              Copy XML
            </button>
          </div>
        </>
      )}

      <div className="flex gap-2">
        <button onClick={onBack} className="btn-ghost">
          Back
        </button>
        <button onClick={onNext} className="btn-primary">
          Next: Validate
        </button>
      </div>
    </div>
  );
}
