"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { api, signOut as apiSignOut } from "@/lib/api";

export type AuthUser = {
  email?: string | null;
  full_name?: string | null;
  is_guest?: boolean;
  email_verified?: boolean;
  pending_email?: string | null;
};

type AuthContextValue = {
  user: AuthUser | null;
  status: "loading" | "ready";
  signedIn: boolean;
  needsVerify: boolean;
  refresh: () => Promise<void>;
  signOut: () => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | null>(null);

const loadingStub: AuthContextValue = {
  user: null,
  status: "loading",
  signedIn: false,
  needsVerify: false,
  refresh: async () => {},
  signOut: async () => {},
};

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [status, setStatus] = useState<"loading" | "ready">("loading");

  const refresh = useCallback(async () => {
    try {
      const me = await api<AuthUser>("/api/auth/me");
      setUser(me);
    } catch {
      setUser(null);
    } finally {
      setStatus("ready");
    }
  }, []);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const me = await api<AuthUser>("/api/auth/me");
        if (!cancelled) setUser(me);
      } catch {
        if (!cancelled) setUser(null);
      } finally {
        if (!cancelled) setStatus("ready");
      }
    })();

    const onFocus = () => {
      void refresh();
    };
    window.addEventListener("focus", onFocus);
    window.addEventListener("pageshow", onFocus);

    return () => {
      cancelled = true;
      window.removeEventListener("focus", onFocus);
      window.removeEventListener("pageshow", onFocus);
    };
  }, [refresh]);

  const signOut = useCallback(async () => {
    await apiSignOut();
    setUser(null);
    setStatus("ready");
  }, []);

  const signedIn = Boolean(user && !user.is_guest);
  const needsVerify = signedIn && Boolean(user && (!user.email_verified || user.pending_email));

  const value = useMemo(
    () => ({ user, status, signedIn, needsVerify, refresh, signOut }),
    [user, status, signedIn, needsVerify, refresh, signOut],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  return useContext(AuthContext) ?? loadingStub;
}
