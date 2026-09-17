"use client";

import { useEffect } from "react";
import { useSearchParams } from "next/navigation";
import { api } from "@/lib/api";
import { trackAdsSignup } from "@/lib/ads";

/**
 * Fires Google Ads sign_up once when landing with ?signup=1
 * (email register + OAuth new accounts).
 * Uses force:true so a prior failed/stub attempt cannot block Tag Assistant verification.
 */
export function SignupConversionBeacon() {
  const params = useSearchParams();

  useEffect(() => {
    if (params.get("signup") !== "1") return;
    let cancelled = false;
    (async () => {
      let email: string | undefined;
      try {
        const me = await api<{ email?: string; is_guest?: boolean }>("/api/auth/me");
        if (!me.is_guest) email = me.email || undefined;
      } catch {
        /* still fire conversion without enhanced email */
      }
      if (!cancelled) {
        await trackAdsSignup({ email, method: "email", force: true });
      }
      if (typeof window !== "undefined" && window.history.replaceState) {
        const url = new URL(window.location.href);
        url.searchParams.delete("signup");
        window.history.replaceState({}, "", url.pathname + url.search + url.hash);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [params]);

  return null;
}
