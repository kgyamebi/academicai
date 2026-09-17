"use client";

import { useEffect } from "react";
import { useSearchParams } from "next/navigation";
import { apiUrl } from "@/lib/utils";
import { trackAdsSignup } from "@/lib/ads";

/**
 * Fires Google Ads sign_up once when landing with ?signup=1 (OAuth new accounts).
 */
export function SignupConversionBeacon() {
  const params = useSearchParams();

  useEffect(() => {
    if (params.get("signup") !== "1") return;
    let cancelled = false;
    (async () => {
      let email: string | undefined;
      try {
        const res = await fetch(`${apiUrl()}/api/auth/me`, { credentials: "include" });
        if (res.ok) {
          const me = (await res.json()) as { email?: string };
          email = me.email;
        }
      } catch {
        /* still fire conversion without enhanced email */
      }
      if (!cancelled) trackAdsSignup({ email, method: "oauth" });
      // Drop the query flag so refresh does not re-signal intent (sessionStorage also guards).
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
