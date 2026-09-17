"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { usePathname } from "next/navigation";
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

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const path = usePathname();
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
    return () => {
      cancelled = true;
    };
  }, [path]);

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
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return ctx;
}
