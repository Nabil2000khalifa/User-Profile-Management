import { createContext, useContext, useEffect, useMemo, useState } from "react";

import { api, ApiError } from "./api/client";
import type { Admin } from "./types";

type AuthContextValue = {
  admin: Admin | null;
  loading: boolean;
  error: string | null;
  login: (email: string, password: string) => Promise<ApiError | null>;
  logout: () => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [admin, setAdmin] = useState<Admin | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.me()
      .then(setAdmin)
      .catch((reason: unknown) => {
        if (!(reason instanceof ApiError && reason.status === 401)) {
          setError("Unable to check the current session.");
        }
      })
      .finally(() => setLoading(false));
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      admin,
      loading,
      error,
      async login(email, password) {
        try {
          const result = await api.login(email, password);
          setAdmin(result.admin);
          setError(null);
          return null;
        } catch (reason) {
          const apiError =
            reason instanceof ApiError
              ? reason
              : new ApiError(0, "Unable to connect to the server.");
          return apiError;
        }
      },
      async logout() {
        try {
          await api.logout();
        } finally {
          setAdmin(null);
        }
      },
    }),
    [admin, error, loading],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const value = useContext(AuthContext);
  if (!value) throw new Error("useAuth must be used within AuthProvider");
  return value;
}
