import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { apiFetch } from "../api/client";
import { useAuth } from "../app/auth";

interface Props {
  children: React.ReactNode;
}

export default function ContractWall({ children }: Props) {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [checked, setChecked] = useState(false);
  const [hasContract, setHasContract] = useState(false);

  useEffect(() => {
    let cancelled = false;

    setChecked(false);
    setHasContract(false);

    // Admin no necesita contrato
    if (user?.role === "admin") {
      setHasContract(true);
      setChecked(true);
      return () => {
        cancelled = true;
      };
    }

    apiFetch<{ has_accepted: boolean }>("/contracts/me")
      .then((data) => {
        if (cancelled) return;
        if (data.has_accepted) {
          setHasContract(true);
        } else {
          navigate("/artist/contract", { replace: true });
        }
      })
      .catch(() => {
        if (cancelled) return;
        navigate("/artist/contract", { replace: true });
      })
      .finally(() => {
        if (cancelled) return;
        setChecked(true);
      });

    return () => {
      cancelled = true;
    };
  }, [navigate, user?.id, user?.role, user?.tenant_id]);

  if (!checked) {
    return (
      <div className="min-h-screen bg-gray-950 flex items-center justify-center">
        <p className="text-sm" style={{ color: "var(--mist-d)" }}>Verifying account...</p>
      </div>
    );
  }

  if (!hasContract) return null;

  return <>{children}</>;
}
