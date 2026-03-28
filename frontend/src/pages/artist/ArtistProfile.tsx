import { useAuth } from "../../app/auth";

export default function ArtistProfile() {
  const { user } = useAuth();

  return (
    <div className="p-6 max-w-2xl mx-auto">
      <h1 className="text-xl font-bold text-white mb-6">My Profile</h1>
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-5 space-y-4">
        <div>
          <p className="text-xs text-gray-500 uppercase tracking-wide mb-1">Email</p>
          <p className="text-white text-sm">{user?.email}</p>
        </div>
        <div>
          <p className="text-xs text-gray-500 uppercase tracking-wide mb-1">Role</p>
          <p className="text-white text-sm capitalize">{user?.role}</p>
        </div>
        <div>
          <p className="text-xs text-gray-500 uppercase tracking-wide mb-1">
            Label / Tenant
          </p>
          <p className="text-white text-sm">{user?.tenant_id}</p>
        </div>
        <div>
          <p className="text-xs text-gray-500 uppercase tracking-wide mb-1">User ID</p>
          <p className="text-gray-400 text-sm font-mono">{user?.id}</p>
        </div>
        {user?.artist_id && (
          <div>
            <p className="text-xs text-gray-500 uppercase tracking-wide mb-1">
              Artist ID
            </p>
            <p className="text-gray-400 text-sm font-mono">{user.artist_id}</p>
          </div>
        )}
      </div>
    </div>
  );
}
