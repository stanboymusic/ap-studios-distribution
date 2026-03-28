import { useContext, useEffect, useMemo, useState } from "react";
import { WizardContext } from "../app/WizardProvider";
import { apiFetch } from "../api/client";

interface Artist { id: string; name: string; type: string; }

export default function StepArtist({ onNext, onBack }: any) {
  const { state, dispatch } = useContext(WizardContext);
  const [artists, setArtists] = useState<Artist[]>([]);
  const [query, setQuery] = useState("");
  const [selectedArtistId, setSelectedArtistId] = useState(state.artist_id || "");
  const [isCreating, setIsCreating] = useState(false);
  const [newName, setNewName] = useState("");
  const [newType, setNewType] = useState("SOLO");

  useEffect(() => { loadArtists(); }, []);
  const loadArtists = async () => {
    try { setArtists(await apiFetch<Artist[]>("/artists/")); } catch {}
  };

  const results = useMemo(() => {
    if (!query.trim()) return artists.slice(0, 10);
    return artists.filter(a => a.name.toLowerCase().includes(query.toLowerCase())).slice(0, 10);
  }, [artists, query]);

  const save = async () => {
    let artistId = selectedArtistId;

    if (isCreating) {
      if (!newName.trim()) return alert("Nombre obligatorio");
      const newArtist = await apiFetch<Artist>("/artists/", {
        method: "POST",
        body: JSON.stringify({ name: newName, type: newType }),
      });
      setArtists(prev => [...prev, newArtist]);
      artistId = newArtist.id;
    }

    if (!artistId) return alert("Debe seleccionar un artista");
    const artist = artists.find(a => a.id === artistId) || { id: artistId, name: newName, type: newType };

    dispatch({ type: "UPDATE_ARTIST", payload: { artist_id: artistId, display_name: artist.name } });
    onNext();
  };

  return (
    <div className="space-y-6">
      <h2 style={{ fontSize: 22, fontFamily: "var(--font-display)", color: "#fff" }}>Artist & Rights</h2>

      {!isCreating ? (
        <div>
          <label>Buscar artista</label>
          <input value={query} onChange={e => setQuery(e.target.value)} placeholder="Escribe para buscar..." />
          <div style={{ border: "1px solid var(--border)", borderRadius: 8, marginTop: 8 }}>
            {results.map(a => (
              <button key={a.id} type="button" onClick={() => setSelectedArtistId(a.id)} style={{ display: "block", width: "100%", textAlign: "left", padding: 8 }}>
                {a.name} <span style={{ color: "var(--mist-d)" }}>({a.type})</span>
              </button>
            ))}
          </div>
          <button className="btn-ghost mt-2" onClick={() => setIsCreating(true)}>+ Crear nuevo artista</button>
        </div>
      ) : (
        <div>
          <label>Nombre artístico</label>
          <input value={newName} onChange={e => setNewName(e.target.value)} />
          <label>Tipo</label>
          <select value={newType} onChange={e => setNewType(e.target.value)}>
            <option value="SOLO">SOLO</option>
            <option value="GROUP">GROUP</option>
          </select>
          <button className="btn-ghost mt-2" onClick={() => setIsCreating(false)}>Cancelar</button>
        </div>
      )}

      <div className="flex gap-2">
        <button onClick={onBack} className="btn-ghost">Atrás</button>
        <button onClick={save} className="btn-primary">Continuar</button>
      </div>
    </div>
  );
}
