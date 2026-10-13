import { useEffect, useState } from "react";
import { useAuth } from "../app/auth";

/**
 * <img> para recursos protegidos por JWT (portadas).
 * Un <img src> normal no puede enviar el header Authorization, así que se descarga
 * con fetch autenticado y se muestra como blob. El archivo nunca es público.
 */
export function AuthImage({ src, alt, ...rest }: React.ImgHTMLAttributes<HTMLImageElement> & { src: string }) {
  const [objectUrl, setObjectUrl] = useState<string | null>(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    let revoked: string | null = null;
    let cancelled = false;
    setFailed(false);
    setObjectUrl(null);
    (async () => {
      try {
        const res = await fetch(src, { headers: useAuth.getState().getHeaders(false) });
        if (!res.ok) throw new Error(String(res.status));
        const url = URL.createObjectURL(await res.blob());
        if (cancelled) {
          URL.revokeObjectURL(url);
          return;
        }
        revoked = url;
        setObjectUrl(url);
      } catch {
        if (!cancelled) setFailed(true);
      }
    })();
    return () => {
      cancelled = true;
      if (revoked) URL.revokeObjectURL(revoked);
    };
  }, [src]);

  if (failed) return <div className="text-sm" style={{ color: "var(--mist-d)" }}>No se pudo cargar la portada.</div>;
  if (!objectUrl) return <div style={{ width: 320, height: 320, maxWidth: "100%", borderRadius: 12, background: "rgba(255,255,255,0.04)" }} />;
  return <img src={objectUrl} alt={alt} {...rest} />;
}
