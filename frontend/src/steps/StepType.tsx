import { useState, useContext } from "react";
import { WizardContext } from "../app/WizardProvider";

export default function StepType({ onNext }: any) {
  const { state, dispatch } = useContext(WizardContext);
  const [version, setVersion] = useState(state.ern?.version || "4.3");
  const [profile, setProfile] = useState(state.ern?.profile || "AudioAlbum");

  const handleSubmit = () => {
    dispatch({ type: "UPDATE_ERN", payload: { version, profile } });
    onNext();
  };

  return (
    <div>
      <h2 className="text-xl font-semibold">Configuración ERN</h2>
      <p style={{ color: "var(--mist-d)" }} className="mb-4">Selecciona versión y perfil DDEX</p>

      <div className="mb-4">
        <label htmlFor="ern-version">Versión ERN</label>
        <select
          id="ern-version"
          value={version}
          onChange={(e) => setVersion(e.target.value)}
          className="w-full"
        >
          <option value="4.2">ERN 4.2</option>
          <option value="4.3">ERN 4.3</option>
        </select>
      </div>

      <div className="mb-4">
        <label htmlFor="ern-profile">Perfil</label>
        <select
          id="ern-profile"
          value={profile}
          onChange={(e) => setProfile(e.target.value)}
          className="w-full"
        >
          <option value="AudioAlbum">Audio Album</option>
          <option value="AudioSingle">Audio Single</option>
        </select>
      </div>

      <button onClick={handleSubmit} className="btn-primary mt-4">
        Continuar
      </button>
    </div>
  );
}
