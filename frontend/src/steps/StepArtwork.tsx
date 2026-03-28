import { useState, useContext } from 'react';
import { WizardContext } from '../app/WizardProvider';
import { API_BASE, getApiHeaders } from '../api/client';

export default function StepArtwork({ onNext, onBack }: any) {
  const { state, dispatch } = useContext(WizardContext);
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState<any>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
    }
  };

  const handleUpload = async () => {
    if (!file) return;

    setUploading(true);
    const formData = new FormData();
    formData.append('cover', file);

    try {
      const response = await fetch(`${API_BASE}/assets/cover`, {
        method: 'POST',
        headers: getApiHeaders(undefined, false),
        body: formData,
      });
      const result = await response.json();
      setUploadResult(result);
      if (result.status === 'ok') {
        dispatch({ type: "UPDATE_RELEASE", payload: { artwork: result, artwork_id: result.id } });
        // Update release in backend
        await fetch(`${API_BASE}/releases/${state.id}`, {
          method: 'PUT',
          headers: getApiHeaders(),
          body: JSON.stringify({ artwork_id: result.id })
        });
      }
    } catch (error) {
      console.error('Upload error:', error);
    } finally {
      setUploading(false);
    }
  };

  return (
    <div>
      <h2 className="text-xl font-semibold">[ Assets ]</h2>

      <div className="mt-4">
        <label htmlFor="coverArt">Cover Art:</label>
        <input
          id="coverArt"
          type="file"
          accept="image/jpeg,image/png"
          onChange={handleFileChange}
          className="border w-full"
        />

        {file && (
          <div className="mt-2">
            <button
              onClick={handleUpload}
              disabled={uploading}
              className="btn-primary disabled:opacity-50"
            >
              {uploading ? 'Subiendo...' : 'Subir Imagen'}
            </button>
          </div>
        )}

        {uploadResult && uploadResult.status === 'ok' && (
          <div className="mt-2 font-bold" style={{ color: "var(--success)" }}>
            [OK] {uploadResult.width}x{uploadResult.height} {uploadResult.format}
          </div>
        )}

        {uploadResult && uploadResult.detail && (
          <div className="mt-2 font-bold" style={{ color: "var(--wine-ll)" }}>
            [ERROR] {uploadResult.detail}
          </div>
        )}
      </div>

      <div className="mt-4 text-sm" style={{ color: "var(--mist-d)" }}>
        Requisitos: 3000x3000 px mínimo, JPG o PNG, RGB
      </div>

      <div className="mt-4 flex gap-2">
        <button onClick={onBack} className="btn-ghost">
          Atrás
        </button>
        <button
          onClick={onNext}
          disabled={!uploadResult || uploadResult.status !== 'ok'}
          className="btn-primary disabled:opacity-50"
        >
          Continuar
        </button>
      </div>
    </div>
  );
}
