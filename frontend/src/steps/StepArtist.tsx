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
        <h2 style={{ fontSize: 22, fontFamily: "var(--font-display)", fontWeight: 300, color: "#fff" }}>Artist & Rights</h2>
        <p className="text-sm" style={{ color: "var(--mist-d)" }}>Identificación única del artista para distribución</p>
      </header>

      <div style={{ background: "var(--card)", border: "0.5px solid var(--border)", borderRadius: 12, padding: "20px 24px" }} className="space-y-6">
        {!isCreating ? (
          <div className="space-y-2">
            <label
              htmlFor="artist-select"
              style={{ fontSize: 12 }}
            >
              Seleccionar Artista:
            </label>
            <div className="flex gap-2">
              <select
                id="artist-select"
                aria-label="Seleccionar artista"
              className="flex-1"
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
                className="btn-ghost"
              >
                + Nuevo
              </button>
            </div>
          </div>
        ) : (
          <div className="space-y-4 p-4 rounded-lg" style={{ border: "1px dashed rgba(107,26,46,0.4)", background: "rgba(107,26,46,0.06)" }}>
            <div className="flex justify-between items-center">
              <h3 className="text-sm font-bold" style={{ color: "var(--wine-ll)" }}>CREAR NUEVO ARTISTA</h3>
              <button onClick={() => setIsCreating(false)} className="text-sm" style={{ color: "var(--wine-ll)" }}>
                Cancelar
              </button>
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <label style={{ fontSize: 12 }}>
                  Nombre Artístico
                </label>
                <input
                  className="w-full"
                  value={newName}
                  onChange={(e) => setNewName(e.target.value)}
                  placeholder="Ej: Stan"
                />
              </div>
              <div className="space-y-2">
                <label
                  htmlFor="artist-type-select"
                  style={{ fontSize: 12 }}
                >
                  Tipo
                </label>
                <select
                  id="artist-type-select"
                  aria-label="Tipo de artista"
                  className="w-full"
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

        <div className="grid grid-cols-2 gap-6 pt-4 text-sm" style={{ borderTop: "0.5px solid var(--border)" }}>
          <div className="space-y-1">
            <p style={{ color: "var(--mist-d)" }}>Distribuidora</p>
            <p style={{ color: "var(--mist)", fontWeight: 500 }}>AP Studios</p>
          </div>
          <div className="space-y-1">
            <p style={{ color: "var(--mist-d)" }}>DPID</p>
            <p className="font-mono" style={{ color: "var(--mist)" }}>PA-DPIDA-202402050E-4</p>
          </div>
        </div>
      </div>

      <div className="flex justify-between gap-4 pt-4">
        <button onClick={onBack} className="btn-ghost">
          Atrás
        </button>
        <button onClick={save} className="btn-primary">
          Continuar
        </button>
      </div>
    </div>
  );
}
