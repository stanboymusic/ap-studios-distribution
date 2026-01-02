import { useState } from 'react';

export default function StepArtwork({ onNext, onBack }: any) {
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
      const response = await fetch('http://127.0.0.1:8000/api/assets/cover', {
        method: 'POST',
        body: formData,
      });
      const result = await response.json();
      setUploadResult(result);
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
        <label htmlFor="coverArt" className="block text-sm font-medium mb-2">Cover Art:</label>
        <input
          id="coverArt"
          type="file"
          accept="image/jpeg,image/png"
          onChange={handleFileChange}
          className="border p-2 w-full"
        />

        {file && (
          <div className="mt-2">
            <button
              onClick={handleUpload}
              disabled={uploading}
              className="px-4 py-2 bg-blue-500 text-white rounded disabled:opacity-50"
            >
              {uploading ? 'Subiendo...' : 'Subir Imagen'}
            </button>
          </div>
        )}

        {uploadResult && uploadResult.status === 'ok' && (
          <div className="mt-2 text-green-600">
            ✔ {uploadResult.width}x{uploadResult.height} {uploadResult.format}
          </div>
        )}

        {uploadResult && uploadResult.detail && (
          <div className="mt-2 text-red-600">
            ❌ {uploadResult.detail}
          </div>
        )}
      </div>

      <div className="mt-4 text-sm text-gray-600">
        Requisitos: 3000x3000 px mínimo, JPG o PNG, RGB
      </div>

      <div className="mt-4 flex gap-2">
        <button onClick={onBack} className="px-4 py-2 border rounded">
          Atrás
        </button>
        <button
          onClick={onNext}
          disabled={!uploadResult || uploadResult.status !== 'ok'}
          className="px-4 py-2 bg-black text-white rounded disabled:opacity-50"
        >
          Continuar
        </button>
      </div>
    </div>
  );
}