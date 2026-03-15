import { useContext, useState, useEffect } from "react";
import { WizardContext } from "../app/WizardProvider";
import { apiFetch } from "../api/client";

interface Artist {
  id: string;
  name: string;
  type: string;
}

export default function StepArtist({ onNext, onBack }: any) {
  const { state, dispatch } = useContext(WizardContext);
  const [artists, setArtists] = useState<Artist[]>([]);
  const [selectedArtistId, setSelectedArtistId] = useState("");
  const [isCreating, setIsCreating] = useState(false);
  const [newName, setNewName] = useState("");
  const [newType, setNewType] = useState("SOLO");

  useEffect(() => {
    loadArtists();
  }, []);

  useEffect(() => {
    if (state.artist_id) {
      setSelectedArtistId(state.artist_id);
    }
  }, [state.artist_id]);

  const loadArtists = async () => {
    try {
      const data = await apiFetch<Artist[]>("/artists/");
      setArtists(data);
    } catch (error) {
      console.error("Error loading artists:", error);
    }
  };

  const save = async () => {
    let artistId = selectedArtistId;

    if (isCreating) {
      if (!newName) return alert("Nombre obligatorio");
      try {
        const newArtist = await apiFetch<Artist>("/artists/", {
          method: "POST",
          body: JSON.stringify({ name: newName, type: newType }),
        });
        artistId = newArtist.id;
        setArtists([...artists, newArtist]);
      } catch (error) {
        return alert("Error al crear artista");
      }
    }

    if (!artistId) return alert("Debe seleccionar un artista");

    const artist = artists.find(a => a.id === artistId) || { name: newName, id: artistId };

    dispatch({
      type: "UPDATE_ARTIST",
      payload: {
        artist_id: artistId,
        display_name: artist.name,
      },
    });
    onNext();
  };

  return (
    <div className="space-y-6">
      <header>
        <h2 className="text-2xl font-semibold text-[#1B4079]">Artist & Rights</h2>
        <p className="text-sm text-[#4D7C8A]">Identificación única del artista para distribución</p>
      </header>

      <div className="bg-white p-6 rounded-xl border border-gray-100 shadow-sm space-y-6">
        {!isCreating ? (
          <div className="space-y-2">
            <label htmlFor="artist-select" className="text-sm font-medium text-gray-700">
              Seleccionar Artista:
            </label>
            <div className="flex gap-2">
              <select
                id="artist-select"
                aria-label="Seleccionar artista"
                className="flex-1 border rounded-lg p-2.5 bg-gray-50 focus:ring-2 focus:ring-[#1B4079] outline-none"
                value={selectedArtistId}
                onChange={(e) => setSelectedArtistId(e.target.value)}
              >
                <option value="">-- Seleccione un artista --</option>
                {artists.map((a) => (
                  <option key={a.id} value={a.id}>
                    {a.name} ({a.type})
                  </option>
                ))}
              </select>
              <button 
                onClick={() => setIsCreating(true)}
                className="px-4 py-2 text-sm font-medium text-[#1B4079] bg-[#1B4079]/10 rounded-lg hover:bg-[#1B4079]/20 transition-colors"
              >
                + Nuevo
              </button>
            </div>
          </div>
        ) : (
          <div className="space-y-4 p-4 border border-dashed border-[#1B4079]/30 rounded-lg bg-blue-50/30">
            <div className="flex justify-between items-center">
              <h3 className="text-sm font-bold text-[#1B4079]">CREAR NUEVO ARTISTA</h3>
              <button onClick={() => setIsCreating(false)} className="text-xs text-red-500 hover:underline">Cancelar</button>
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <label className="text-xs font-medium text-gray-500">Nombre Artístico</label>
                <input
                  className="w-full border rounded-lg p-2 bg-white outline-none focus:ring-2 focus:ring-[#1B4079]"
                  value={newName}
                  onChange={(e) => setNewName(e.target.value)}
                  placeholder="Ej: Stan"
                />
              </div>
              <div className="space-y-2">
                <label htmlFor="artist-type-select" className="text-xs font-medium text-gray-500">
                  Tipo
                </label>
                <select
                  id="artist-type-select"
                  aria-label="Tipo de artista"
                  className="w-full border rounded-lg p-2 bg-white outline-none focus:ring-2 focus:ring-[#1B4079]"
                  value={newType}
                  onChange={(e) => setNewType(e.target.value)}
                >
                  <option value="SOLO">SOLO</option>
                  <option value="GROUP">GROUP</option>
                </select>
              </div>
            </div>
          </div>
        )}

        <div className="grid grid-cols-2 gap-6 pt-4 border-t border-gray-50 text-sm">
          <div className="space-y-1">
            <p className="text-gray-400 font-medium">Distribuidora</p>
            <p className="text-[#1B4079] font-semibold">AP Studios</p>
          </div>
          <div className="space-y-1">
            <p className="text-gray-400 font-medium">DPID</p>
            <p className="text-[#1B4079] font-mono">PA-DPIDA-202402050E-4</p>
          </div>
        </div>
      </div>

      <div className="flex justify-between gap-4 pt-4">
        <button 
          onClick={onBack} 
          className="px-6 py-2.5 border border-gray-200 rounded-lg text-gray-600 hover:bg-gray-50 font-medium transition-all"
        >
          Atrás
        </button>
        <button 
          onClick={save} 
          className="px-8 py-2.5 bg-[#1B4079] text-white rounded-lg font-medium hover:bg-[#14305c] shadow-md transition-all"
        >
          Continuar
        </button>
      </div>
    </div>
  );
}
