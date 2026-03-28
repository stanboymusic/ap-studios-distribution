import { useMemo, useState } from "react";
import { Button } from "../components/ui/Button";
import { Card, CardContent } from "../components/ui/Card";
import { setAuthSession, type UserRole } from "../app/auth";

export default function AuthGateway({ onSignedIn }: { onSignedIn: () => void }) {
  const [role, setRole] = useState<UserRole>("artist");
  const [name, setName] = useState("");

  const placeholder = useMemo(() => (role === "admin" ? "ap-admin" : "artist-username"), [role]);

  const handleEnter = () => {
    const clean = name.trim() || placeholder;
    setAuthSession(role, clean.toLowerCase().replace(/\s+/g, "-"));
    onSignedIn();
  };

  return (
    <div className="min-h-screen bg-[#F6F8F9] flex items-center justify-center p-6">
      <Card className="w-full max-w-xl rounded-2xl border-none shadow-sm">
        <CardContent className="space-y-6">
          <div>
            <h1 className="text-2xl font-semibold text-[#1B4079]">AP Studios Access</h1>
            <p className="text-sm text-[#4D7C8A] mt-1">
              Selecciona tu tipo de acceso para entrar al portal correcto.
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <button
              className={`rounded-xl border px-4 py-4 text-left ${
                role === "artist" ? "border-[#1B4079] bg-[#EAF0F2]" : "border-gray-200 bg-white"
              }`}
              onClick={() => setRole("artist")}
            >
              <div className="text-sm font-semibold text-[#1B4079]">Artist Portal</div>
              <div className="text-sm text-[#4D7C8A] mt-1">Subir canciones y revisar estado.</div>
            </button>
            <button
              className={`rounded-xl border px-4 py-4 text-left ${
                role === "admin" ? "border-[#1B4079] bg-[#EAF0F2]" : "border-gray-200 bg-white"
              }`}
              onClick={() => setRole("admin")}
            >
              <div className="text-sm font-semibold text-[#1B4079]">AP Admin</div>
              <div className="text-sm text-[#4D7C8A] mt-1">Aprobar, rechazar y despachar releases.</div>
            </button>
          </div>

          <div className="space-y-2">
            <label className="text-sm text-[#4D7C8A]">User ID</label>
            <input
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full rounded-xl border border-gray-200 px-3 py-2 text-sm"
              placeholder={placeholder}
            />
          </div>

          <div className="flex justify-end">
            <Button onClick={handleEnter}>Enter</Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
