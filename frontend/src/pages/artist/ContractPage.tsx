import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { apiFetch } from "../../api/client";

const TERMS_VERSION = "1.0.0";

const TERMS_TEXT = `
TÉRMINOS Y CONDICIONES DE DISTRIBUCIÓN — AP Studios v${TERMS_VERSION}

1. PARTES
   AP Studios (el "Distribuidor") y el artista registrado (el "Artista").

2. LICENCIA DE DISTRIBUCIÓN
   El Artista otorga a AP Studios una licencia no exclusiva para distribuir,
   promocionar y monetizar su música en plataformas digitales a nivel mundial.

3. DERECHOS DEL ARTISTA
   El Artista retiene el 100% de sus derechos de autor. AP Studios actúa
   únicamente como intermediario de distribución.

4. ROYALTIES
   AP Studios aplica una comisión de distribución acordada por separado.
   Los pagos se realizan conforme al calendario de pagos vigente.

5. CONTENIDO
   El Artista garantiza que posee los derechos necesarios sobre todo el
   contenido que sube a la plataforma y que no infringe derechos de terceros.

6. IDENTIFICADORES
   AP Studios asigna UPC e ISRC según los estándares internacionales DDEX.
   El DPID operador es PA-DPIDA-202402050E-4.

7. TERMINACIÓN
   Cualquiera de las partes puede terminar el acuerdo con 30 días de aviso.
   Las releases en distribución activa continuarán hasta el siguiente ciclo.

8. LEY APLICABLE
   Este acuerdo se rige por las leyes de la República Bolivariana de Venezuela.
`;

export default function ContractPage() {
  const navigate = useNavigate();
  const [accepted, setAccepted] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleAccept = async () => {
    if (!accepted) return;
    setLoading(true);
    setError(null);
    try {
      await apiFetch("/contracts/accept", {
        method: "POST",
        body: JSON.stringify({
          accepted: true,
          version: TERMS_VERSION,
        }),
      });
      navigate("/artist", { replace: true });
    } catch (e: any) {
      setError(e.message ?? "Error accepting contract");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center px-4 py-10">
      <div className="w-full max-w-[760px] fade-up">
        {/* Header */}
        <div className="mb-6 text-center">
          <h1 className="page-title" style={{ fontSize: 30 }}>
            AP Studios
          </h1>
          <p className="page-subtitle" style={{ fontSize: 15 }}>
            Distribution Agreement - v{TERMS_VERSION}
          </p>
        </div>

        {/* Contract card */}
        <div className="card">
          {/* Terms scroll area */}
          <div
            className="h-[360px] overflow-y-auto p-5"
            style={{
              borderBottom: "0.5px solid var(--border)",
              background: "var(--surface)",
            }}
          >
            <pre
              style={{
                color: "var(--mist)",
                fontSize: 14,
                lineHeight: 1.6,
                whiteSpace: "pre-wrap",
                fontFamily: "var(--font-body)",
              }}
            >
              {TERMS_TEXT.trim()}
            </pre>
          </div>

          {/* Accept section */}
          <div className="p-5">
            {error && (
              <div
                style={{
                  marginBottom: 16,
                  padding: "8px 10px",
                  background: "rgba(168,56,90,0.12)",
                  border: "0.5px solid rgba(168,56,90,0.35)",
                  borderRadius: 8,
                  color: "#E8C98A",
                  fontSize: 14,
                }}
              >
                {error}
              </div>
            )}

            <label className="flex items-start gap-3 cursor-pointer">
              <input
                type="checkbox"
                checked={accepted}
                onChange={(e) => setAccepted(e.target.checked)}
                style={{ accentColor: "var(--wine-ll)" }}
                className="mt-0.5 w-4 h-4 cursor-pointer"
              />
              <span style={{ color: "var(--mist)", fontSize: 16, lineHeight: 1.6 }}>
                He leído y acepto los Términos y Condiciones de Distribución de AP Studios v{TERMS_VERSION}. Entiendo
                que esta aceptación queda registrada con fecha, hora e IP para efectos legales.
              </span>
            </label>

            <button
              onClick={handleAccept}
              disabled={!accepted || loading}
              className="btn-primary w-full justify-center mt-5"
            >
              {loading ? "Registering acceptance..." : "Accept & Continue"}
            </button>

            <p
              className="text-center mt-3"
              style={{ color: "var(--mist-d)", fontSize: 13 }}
            >
              DPID: PA-DPIDA-202402050E-4 - AP Studios Distribution
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
