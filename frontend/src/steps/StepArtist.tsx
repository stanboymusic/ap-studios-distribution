import { useContext, useState } from "react";
import { WizardContext } from "../app/WizardProvider";

export default function StepArtist({ onNext, onBack }: any) {
  const { dispatch } = useContext(WizardContext);
  const [name, setName] = useState("");

  const save = () => {
    if (!name) return alert("Nombre obligatorio");
    dispatch({
      type: "UPDATE_ARTIST",
      payload: {
        display_name: name,
        country: "US",
        primary_language: "es",
        is_rights_holder: true,
      },
    });
    onNext();
  };

  return (
    <div>
      <h2 className="text-xl font-semibold">[ Artist & Rights ]</h2>

      <div className="mt-4 space-y-4">
        <div className="flex items-center">
          <label className="w-32">Artista principal:</label>
          <input
            className="border p-2 flex-1"
            placeholder="Nombre artístico"
            value={name}
            onChange={(e) => setName(e.target.value)}
          />
        </div>

        <div className="flex items-center">
          <label className="w-32">Tipo:</label>
          <div className="flex items-center">
            <input type="radio" checked readOnly className="mr-2" aria-label="Solista" />
            <span>Solista</span>
          </div>
        </div>

        <div className="flex items-center">
          <label className="w-32">Distribuidora:</label>
          <span className="text-gray-700">AP Studios</span>
        </div>

        <div className="flex items-center">
          <label className="w-32">DPID:</label>
          <span className="text-gray-700">PA-DPIDA-202402050E-4</span>
        </div>

        <div className="flex items-center">
          <label className="w-32">Rol:</label>
          <span className="text-gray-700">Rights Controller</span>
        </div>
      </div>

      <div className="mt-4 flex gap-2">
        <button onClick={onBack} className="px-4 py-2 border rounded">
          Atrás
        </button>
        <button onClick={save} className="px-4 py-2 bg-black text-white rounded">
          Continuar
        </button>
      </div>
    </div>
  );
}