import { useContext, useState, useEffect } from "react";
import { WizardContext } from "../app/WizardProvider";
import { API_BASE, getApiHeaders } from "../api/client";

export default function StepTracks({ onNext, onBack }: any) {
  const { state, dispatch } = useContext(WizardContext);
  const [title, setTitle] = useState("");
  const [trackNumber, setTrackNumber] = useState(1);
  const [isrc, setIsrc] = useState("");
  const [explicit, setExplicit] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [tracks, setTracks] = useState<any[]>([]);

  useEffect(() => {
    if (state.tracks) {
      console.log('DEBUG: Loading tracks from state:', state.tracks);
      setTracks(state.tracks);
      setTrackNumber(state.tracks.length + 1);
    }
  }, [state.tracks]);

  const addTrack = async () => {
    if (!title || !file) {
      alert("Título y archivo de audio obligatorios");
      return;
    }

    const formData = new FormData();
    formData.append('release_id', state.id);
    formData.append('title', title);
    formData.append('track_number', trackNumber.toString());
    formData.append('explicit', explicit.toString());
    if (isrc) formData.append('isrc', isrc);
    formData.append('audio', file);

    try {
      console.log('DEBUG: Adding track...', { title, trackNumber, explicit, file: file.name });

      const res = await fetch(`${API_BASE}/tracks/`, {
        method: "POST",
        headers: getApiHeaders(undefined, false),
        body: formData,
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(data?.detail || "API Error");
      }

      console.log('DEBUG: Track response:', data);

      if (data.error) {
        alert("Error del servidor: " + data.error);
        return;
      }

      const newTrack = {
        track_id: data.track_id,
        title: data.title,
        track_number: data.track_number,
        duration_seconds: data.duration_seconds,
        explicit: data.explicit,
        isrc: data.isrc,
        file_path: data.file_path
      };

      const updatedTracks = [...tracks, newTrack];
      setTracks(updatedTracks);
      dispatch({ type: "UPDATE_TRACKS", payload: updatedTracks });

      // Reset form
      setTitle("");
      setTrackNumber(trackNumber + 1);
      setIsrc("");
      setExplicit(false);
      setFile(null);
    } catch (error) {
      console.error(error);
      alert("Error al añadir track");
    }
  };

  const handleNext = () => {
    if (tracks.length === 0) {
      alert("Debes añadir al menos un track para continuar");
      return;
    }
    onNext();
  };

  return (
    <div>
      <h2 className="text-xl font-semibold">Tracks</h2>

      <div className="mb-4">
        <label>Título del track:</label>
        <input
          className="border w-full mt-1"
          placeholder="Título del track"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
        />
      </div>

      <div className="mb-4">
        <label>Número de track:</label>
        <input
          type="number"
          className="border w-full mt-1"
          placeholder="1"
          value={trackNumber}
          onChange={(e) => setTrackNumber(Number(e.target.value))}
        />
      </div>

      <div className="mb-4">
        <label>ISRC:</label>
        <input
          className="border w-full mt-1"
          placeholder="Ej: QM-ABC-24-00001"
          value={isrc}
          onChange={(e) => setIsrc(e.target.value)}
        />
      </div>

      <div className="mb-4">
        <label htmlFor="explicitCheck">Explícito:</label>
        <input
          id="explicitCheck"
          type="checkbox"
          title="Marcar si el contenido es explícito"
          checked={explicit}
          onChange={(e) => setExplicit(e.target.checked)}
        />
      </div>

      <div className="mb-4">
        <label htmlFor="audioFile">Archivo de audio:</label>
        <input
          id="audioFile"
          type="file"
          accept="audio/*"
          title="Selecciona un archivo de audio"
          onChange={(e) => setFile(e.target.files?.[0] || null)}
        />
      </div>

      <button onClick={addTrack} className="btn-primary mb-4">
        Añadir track
      </button>

      <div>
        <h3 className="text-lg font-semibold">Tracks añadidos:</h3>
        <ul>
          {tracks.map((track, index) => (
            <li key={index} className="border p-3 mb-2">
              {track.track_number}. {track.title} - {track.duration_seconds}s {track.explicit ? '(Explícito)' : ''}
            </li>
          ))}
        </ul>
      </div>

      <div className="mt-4 flex gap-2">
        <button onClick={onBack} className="btn-ghost">
          Atrás
        </button>
        <button onClick={handleNext} className="btn-primary">
          Continuar
        </button>
      </div>
    </div>
  );
}
