import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "../app/auth";

interface Props {
  children: React.ReactNode;
  requiredRole?: "admin" | "artist" | "staff";
}

export default function ProtectedRoute({ children, requiredRole }: Props) {
  const { isAuthenticated, user } = useAuth();
  const location = useLocation();

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  if (requiredRole && user?.role !== requiredRole && user?.role !== "admin") {
    return <Navigate to={user?.role === "artist" ? "/artist" : "/login"} replace />;
  }

  return <>{children}</>;
}
