import { useContext, useState, useEffect, useMemo } from "react";
import { WizardContext } from "../app/WizardProvider";
import { apiFetch } from "../api/client";

interface Artist {
  id: string;
  name: string;
  type: string;
}

const SearchIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" aria-hidden="true">
    <path d="M11 3a8 8 0 1 1 0 16 8 8 0 0 1 0-16Zm10 18-4.35-4.35" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
  </svg>
);

export default function StepArtist({ onNext, onBack }: any) {
  const { state, dispatch } = useContext(WizardContext);
  const [artists, setArtists] = useState<Artist[]>([]);
  const [selectedArtistId, setSelectedArtistId] = useState("");
  const [isCreating, setIsCreating] = useState(false);
  const [newName, setNewName] = useState("");
  const [newType, setNewType] = useState("SOLO");
  const [query, setQuery] = useState("");
  const [showDropdown, setShowDropdown] = useState(false);

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

  const selectedArtist = useMemo(() => artists.find((a) => a.id === selectedArtistId), [artists, selectedArtistId]);
  const results = useMemo(() => {
    if (!query.trim()) return artists.slice(0, 8);
    return artists.filter((a) => a.name.toLowerCase().includes(query.toLowerCase())).slice(0, 8);
  }, [artists, query]);

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
      } catch {
        return alert("Error al crear artista");
      }
    }

    if (!artistId) return alert("Debe seleccionar un artista");

    const artist = artists.find((a) => a.id === artistId) || { name: newName, id: artistId };

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
      </header>

      <div style={{ background: "var(--card)", border: "0.5px solid var(--border)", borderRadius: 12, padding: "20px 24px" }} className="space-y-6">
        {!isCreating ? (
          <div className="space-y-2" style={{ position: "relative" }}>
            <label style={{ fontSize: 12 }}>Buscar artista</label>
            {!selectedArtist ? (
              <>
                <div style={{ position: "relative" }}>
                  <div style={{ position: "absolute", left: 10, top: 10, color: "var(--mist-d)" }}><SearchIcon /></div>
                  <input
                    value={query}
                    onChange={(e) => {
                      setQuery(e.target.value);
                      setShowDropdown(true);
                    }}
                    onFocus={() => setShowDropdown(true)}
                    placeholder="Escribe para buscar..."
                    style={{ paddingLeft: 34 }}
                  />
                </div>
                {showDropdown && (
                  <div style={{ background: "#111", border: "0.5px solid var(--border)", borderRadius: 10, marginTop: 8, maxHeight: 220, overflowY: "auto" }}>
                    {results.map((artist) => (
                      <button key={artist.id} type="button" onClick={() => { setSelectedArtistId(artist.id); setShowDropdown(false); }} style={{ width: "100%", display: "flex", gap: 12, alignItems: "center", textAlign: "left", padding: "10px 12px", borderBottom: "0.5px solid var(--border)", color: "var(--mist)" }}>
                        <div style={{ width: 28, height: 28, borderRadius: "50%", background: "rgba(107,26,46,0.25)", display: "grid", placeItems: "center", fontSize: 11, color: "var(--wine-ll)" }}>{artist.name.slice(0, 2).toUpperCase()}</div>
                        <div>
                          <div style={{ fontSize: 14 }}>{artist.name}</div>
                          <div style={{ fontSize: 11, color: "var(--mist-d)" }}>{artist.type}</div>
                        </div>
                      </button>
                    ))}
                    <button type="button" onClick={() => setIsCreating(true)} style={{ width: "100%", textAlign: "left", padding: "10px 12px", color: "var(--wine-ll)" }}>
                      + Crear nuevo artista
                    </button>
                  </div>
                )}
              </>
            ) : (
              <div style={{ background: "rgba(107,26,46,0.08)", border: "0.5px solid var(--border)", borderRadius: 10, padding: 14, display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <div>
                  <div style={{ color: "var(--mist)", fontSize: 15 }}>{selectedArtist.name}</div>
                  <div style={{ color: "var(--mist-d)", fontSize: 12 }}>{selectedArtist.type}</div>
                </div>
                <button className="btn-ghost" onClick={() => setSelectedArtistId("")}>Cambiar</button>
              </div>
            )}
          </div>
        ) : (
          <div className="space-y-4 p-4 rounded-lg" style={{ border: "1px dashed rgba(107,26,46,0.4)", background: "rgba(107,26,46,0.06)" }}>
            <div className="flex justify-between items-center">
              <h3 className="text-sm font-bold" style={{ color: "var(--wine-ll)" }}>CREAR NUEVO ARTISTA</h3>
              <button onClick={() => setIsCreating(false)} className="text-sm" style={{ color: "var(--wine-ll)" }}>Cancelar</button>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <label style={{ fontSize: 12 }}>Nombre Artístico</label>
                <input className="w-full" value={newName} onChange={(e) => setNewName(e.target.value)} placeholder="Ej: Stan" />
              </div>
              <div className="space-y-2">
                <label htmlFor="artist-type-select" style={{ fontSize: 12 }}>Tipo</label>
                <select id="artist-type-select" className="w-full" value={newType} onChange={(e) => setNewType(e.target.value)}>
                  <option value="SOLO">SOLO</option>
                  <option value="GROUP">GROUP</option>
                </select>
              </div>
            </div>
          </div>
        )}
      </div>

      <div className="flex justify-between gap-4 pt-4">
        <button onClick={onBack} className="btn-ghost">Atrás</button>
        <button onClick={save} className="btn-primary">Continuar</button>
      </div>
    </div>
  );
}
