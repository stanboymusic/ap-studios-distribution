import { Outlet, NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "../app/auth";
import ContractWall from "../components/ContractWall";

const NAV = [
  {
    section: "My Music",
    items: [
      { to: "/artist", label: "My Releases", end: true },
      { to: "/artist/new", label: "New Release" },
      { to: "/artist/earnings", label: "Earnings" },
      { to: "/artist/profile", label: "Profile" },
    ],
  },
];

export default function ArtistLayout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const initials = user?.email?.slice(0, 2).toUpperCase() ?? "AR";
  const accent = "#4A1F52";

  const handleLogout = async () => {
    await logout();
    navigate("/login");
  };

  return (
    <ContractWall>
      <div style={{ display: "flex", minHeight: "100vh" }}>
        {/* Sidebar */}
        <aside
          style={{
            width: 260,
            minWidth: 260,
            background: "linear-gradient(180deg, #130A17 0%, #0D0810 100%)",
            borderRight: "0.5px solid rgba(74,31,82,0.35)",
            display: "flex",
            flexDirection: "column",
            position: "relative",
            overflow: "hidden",
          }}
        >
          {/* Sidebar right glow line */}
          <div
            style={{
              position: "absolute",
              top: 0,
              right: 0,
              width: 1.5,
              height: "100%",
              background: `linear-gradient(180deg,transparent 0%,${accent} 40%,#1A0A1E 70%,transparent 100%)`,
              opacity: 0.5,
            }}
          />

          {/* Logo */}
          <div
            style={{
              padding: "32px 24px 28px",
              borderBottom: "0.5px solid rgba(74,31,82,0.35)",
            }}
          >
            <div
              style={{
                fontFamily: "'Cormorant Garamond', serif",
                fontSize: 26,
                fontWeight: 600,
                letterSpacing: "0.07em",
                textTransform: "uppercase",
                color: "#fff",
              }}
            >
              AP <span style={{ color: accent }}>Studios</span>
            </div>
            <div
              style={{
                fontSize: 11,
                fontWeight: 300,
                letterSpacing: "0.22em",
                textTransform: "uppercase",
                color: "#8A7A90",
                marginTop: 5,
              }}
            >
              Artist Portal
            </div>
            <div
              style={{
                marginTop: 10,
                display: "inline-flex",
                alignItems: "center",
                gap: 5,
                background: "rgba(74,31,82,0.18)",
                border: "0.5px solid rgba(74,31,82,0.4)",
                borderRadius: 3,
                padding: "4px 10px",
                fontSize: 10,
                letterSpacing: "0.12em",
                color: "#C8B8CC",
                textTransform: "uppercase",
              }}
            >
              Artist Portal
            </div>
          </div>

          {/* Nav */}
          <nav style={{ padding: "14px 0", flex: 1, overflowY: "auto" }}>
            {NAV.map(({ section, items }) => (
              <div key={section}>
                <div
                  style={{
                    fontSize: 11,
                    fontWeight: 400,
                    letterSpacing: "0.2em",
                    textTransform: "uppercase",
                    color: "#8A7A90",
                    padding: "14px 24px 7px",
                    opacity: 0.6,
                  }}
                >
                  {section}
                </div>
                {items.map(({ to, label, end }) => (
                  <NavLink
                    key={to}
                    to={to}
                    end={end}
                    style={({ isActive }) => ({
                      display: "flex",
                      alignItems: "center",
                      gap: 12,
                      padding: "13px 24px",
                      fontSize: 14,
                      fontWeight: 300,
                      letterSpacing: "0.03em",
                      color: isActive ? "#fff" : "#8A7A90",
                      background: isActive
                        ? "rgba(74,31,82,0.2)"
                        : "transparent",
                      borderLeft: `2px solid ${
                        isActive ? accent : "transparent"
                      }`,
                      textDecoration: "none",
                      transition: "all 0.2s",
                      position: "relative",
                    })}
                  >
                    <div
                      style={{
                        width: 7,
                        height: 7,
                        borderRadius: "50%",
                        background: "currentColor",
                        opacity: 0.5,
                        flexShrink: 0,
                      }}
                    />
                    {label}
                  </NavLink>
                ))}
              </div>
            ))}
          </nav>

          {/* Footer */}
          <div
            style={{
              padding: "18px 24px",
              borderTop: "0.5px solid rgba(74,31,82,0.35)",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <div
                style={{
                  width: 36,
                  height: 36,
                  borderRadius: "50%",
                  background: `linear-gradient(135deg,${accent} 0%,#2D1230 100%)`,
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  fontSize: 12,
                  fontWeight: 500,
                  color: "#fff",
                  border: "0.5px solid rgba(255,255,255,0.1)",
                  flexShrink: 0,
                }}
              >
                {initials}
              </div>
              <div style={{ flex: 1, minWidth: 0 }}>
                <div
                  style={{
                    fontSize: 14,
                    color: "#C8B8CC",
                    whiteSpace: "nowrap",
                    overflow: "hidden",
                    textOverflow: "ellipsis",
                  }}
                >
                  {user?.email}
                </div>
                <div style={{ fontSize: 12, color: "#8A7A90" }}>
                  Artist
                </div>
              </div>
              <button
                onClick={handleLogout}
                style={{
                  background: "none",
                  border: "none",
                  color: accent,
                  fontSize: 18,
                  cursor: "pointer",
                  padding: 0,
                  lineHeight: 1,
                }}
                title="Sign out"
              >
                x
              </button>
            </div>
          </div>
        </aside>

        {/* Main */}
        <div
          style={{
            flex: 1,
            display: "flex",
            flexDirection: "column",
            overflow: "hidden",
          }}
        >
          {/* Topbar */}
          <header
            style={{
              height: 64,
              flexShrink: 0,
              background:
                "linear-gradient(90deg,rgba(13,8,16,0.98) 0%,rgba(19,10,23,0.98) 100%)",
              borderBottom: "0.5px solid rgba(74,31,82,0.35)",
              display: "flex",
              alignItems: "center",
              padding: "0 32px",
              gap: 14,
              backdropFilter: "blur(12px)",
              position: "sticky",
              top: 0,
              zIndex: 10,
            }}
          >
            <div
              style={{
                fontFamily: "'Cormorant Garamond', serif",
                fontSize: 18,
                fontWeight: 300,
                letterSpacing: "0.12em",
                textTransform: "uppercase",
                color: "#C8B8CC",
              }}
            >
              Artist Portal
            </div>
            <div style={{ flex: 1 }} />
            <button
              onClick={() => navigate("/artist/new")}
              style={{
                display: "inline-flex",
                alignItems: "center",
                gap: 6,
                background: `linear-gradient(135deg,${accent} 0%,#6B1A2E 100%)`,
                border: "0.5px solid rgba(74,31,82,0.4)",
                borderRadius: 8,
                padding: "10px 18px",
                fontSize: 13,
                fontWeight: 400,
                letterSpacing: "0.1em",
                textTransform: "uppercase",
                color: "#fff",
                cursor: "pointer",
                fontFamily: "'DM Sans', sans-serif",
              }}
            >
              + New Release
            </button>
          </header>

          <div className="shimmer" />

          <main style={{ flex: 1, overflowY: "auto" }}>
            <Outlet />
          </main>
        </div>
      </div>
    </ContractWall>
  );
}
