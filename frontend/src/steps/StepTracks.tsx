import { useContext, useState } from "react";
import { WizardContext } from "../app/WizardProvider";
import axios from "axios";

export default function StepTracks({ onNext, onBack }: any) {
  const { state, dispatch } = useContext(WizardContext);
  const [title, setTitle] = useState("");
  const [trackNumber, setTrackNumber] = useState(1);
  const [explicit, setExplicit] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [tracks, setTracks] = useState<any[]>(state.tracks || []);

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
    formData.append('audio', file);

    try {
      const response = await axios.post('http://127.0.0.1:8000/api/tracks', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });

      const newTrack = {
        track_id: response.data.track_id,
        title: response.data.title,
        track_number: response.data.track_number,
        duration_seconds: response.data.duration_seconds,
        explicit: response.data.explicit,
        file_path: response.data.file_path
      };

      const updatedTracks = [...tracks, newTrack];
      setTracks(updatedTracks);
      dispatch({ type: "UPDATE_RELEASE", payload: { ...state.release, tracks: updatedTracks } });

      // Reset form
      setTitle("");
      setTrackNumber(trackNumber + 1);
      setExplicit(false);
      setFile(null);
    } catch (error) {
      console.error(error);
      alert("Error al añadir track");
    }
  };

  return (
    <div>
      <h2 className="text-xl font-semibold">Tracks</h2>

      <div className="mb-4">
        <label>Título del track:</label>
        <input
          className="border p-2 w-full mt-1"
          placeholder="Título del track"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
        />
      </div>

      <div className="mb-4">
        <label>Número de track:</label>
        <input
          type="number"
          className="border p-2 w-full mt-1"
          placeholder="1"
          value={trackNumber}
          onChange={(e) => setTrackNumber(Number(e.target.value))}
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

      <button onClick={addTrack} className="px-4 py-2 bg-blue-500 text-white rounded mb-4">
        Añadir track
      </button>

      <div>
        <h3 className="text-lg font-semibold">Tracks añadidos:</h3>
        <ul>
          {tracks.map((track, index) => (
            <li key={index} className="border p-2 mb-2">
              {track.track_number}. {track.title} - {track.duration_seconds}s {track.explicit ? '(Explícito)' : ''}
            </li>
          ))}
        </ul>
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