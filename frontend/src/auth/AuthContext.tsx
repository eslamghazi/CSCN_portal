import { createContext, useContext, useEffect, useState, ReactNode } from "react";
import { api } from "../api/client";
import { CurrentUser } from "../api/types";

interface AuthState {
  user: CurrentUser | null;
  loading: boolean;
  login: (username: string, password: string, remember: boolean) => Promise<string | null>;
  logout: () => Promise<void>;
  can: (module: string, action: string) => boolean;
  refresh: () => Promise<void>;
}

const AuthContext = createContext<AuthState>(null as any);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<CurrentUser | null>(null);
  const [loading, setLoading] = useState(true);

  async function refresh() {
    try {
      const data = await api.get("/api/auth/me");
      setUser(data.authenticated ? data.user : null);
    } catch {
      setUser(null);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { refresh(); }, []);

  async function login(username: string, password: string, remember: boolean) {
    const res = await api.post("/api/auth/login", { username, password, remember });
    if (res.success) {
      setUser(res.user);
      return null;
    }
    return res.message || "فشل تسجيل الدخول";
  }

  async function logout() {
    try { await api.post("/api/auth/logout"); } catch { /* ignore */ }
    setUser(null);
  }

  function can(module: string, action: string) {
    if (!user) return false;
    if (user.role_name === "superadmin") return true;
    return !!user.permissions?.[module]?.[action];
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, logout, can, refresh }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
