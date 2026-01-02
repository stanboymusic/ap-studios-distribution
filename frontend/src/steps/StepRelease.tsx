import { useContext, useState } from "react";
import { WizardContext } from "../app/WizardProvider";
import axios from "axios";

export default function StepRelease({ onNext, onBack }: any) {
  const { dispatch } = useContext(WizardContext);
  const [title, setTitle] = useState("");
  const [releaseType, setReleaseType] = useState("Single");
  const [originalReleaseDate, setOriginalReleaseDate] = useState("");
  const [language, setLanguage] = useState("es");
  const [territories, setTerritories] = useState("Worldwide");

  const save = async () => {
    if (!title || !originalReleaseDate) return alert("Título y fecha de lanzamiento obligatorios");
    try {
      const response = await axios.post('http://127.0.0.1:8000/api/releases/', {
        title,
        release_type: releaseType,
        original_release_date: originalReleaseDate,
        language,
        territories: [territories]
      });
      dispatch({ type: "SET_ID", payload: response.data.release_id });
      dispatch({
        type: "UPDATE_RELEASE",
        payload: {
          title: { text: title, language },
          release_type: releaseType,
          original_release_date: originalReleaseDate,
          territories: [territories],
          parental_advisory: "None",
          genres: { primary: "Pop" },
        },
      });
      onNext();
    } catch (error) {
      console.error(error);
      alert("Error al crear el release");
    }
  };

  return (
    <div>
      <h2 className="text-xl font-semibold">Release Info</h2>

      <div className="mt-4">
        <label>Título del lanzamiento:</label>
        <input
          className="border p-2 w-full mt-1"
          placeholder="Título del lanzamiento"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          required
        />
      </div>

      <div className="mt-4">
        <label>Tipo de release:</label>
        <select
          className="border p-2 w-full mt-1"
          aria-label="Tipo de release"
          value={releaseType}
          onChange={(e) => setReleaseType(e.target.value)}
        >
          <option value="Single">Single</option>
          <option value="EP">EP</option>
          <option value="Album">Album</option>
        </select>
      </div>

      <div className="mt-4">
        <label>Fecha de lanzamiento:</label>
        <input
          type="date"
          className="border p-2 w-full mt-1"
          placeholder="YYYY-MM-DD"
          value={originalReleaseDate}
          onChange={(e) => setOriginalReleaseDate(e.target.value)}
          required
        />
      </div>

      <div className="mt-4">
        <label>Idioma principal:</label>
        <input
          className="border p-2 w-full mt-1"
          placeholder="es"
          value={language}
          onChange={(e) => setLanguage(e.target.value)}
        />
      </div>

      <div className="mt-4">
        <label>Territorios:</label>
        <input
          className="border p-2 w-full mt-1"
          placeholder="Worldwide"
          value={territories}
          onChange={(e) => setTerritories(e.target.value)}
        />
      </div>

      <div className="mt-4 flex gap-2">
        <button onClick={onBack} className="px-4 py-2 border rounded">
          Atrás
        </button>
        <button onClick={save} className="px-4 py-2 bg-black text-white rounded">
          Guardar y continuar
        </button>
      </div>
    </div>
  );
}