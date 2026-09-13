"use client";

import { useEffect } from "react";

/**
 * Browser Sentry (Invoice App pattern). No-ops unless NEXT_PUBLIC_SENTRY_DSN is set.
 */
export function SentryInit() {
  useEffect(() => {
    const dsn = process.env.NEXT_PUBLIC_SENTRY_DSN;
    if (!dsn) return;
    let cancelled = false;
    (async () => {
      try {
        const Sentry = await import("@sentry/browser");
        if (cancelled) return;
        Sentry.init({
          dsn,
          environment:
            process.env.NEXT_PUBLIC_SENTRY_ENVIRONMENT ||
            process.env.NEXT_PUBLIC_APP_ENV ||
            "development",
          release: process.env.NEXT_PUBLIC_SENTRY_RELEASE || "academiccheck-web@1.0.0",
          tracesSampleRate: process.env.NODE_ENV === "production" ? 0.05 : 0.1,
          sendDefaultPii: false,
        });
        window.addEventListener("unhandledrejection", (event) => {
          Sentry.captureException(event.reason ?? new Error("unhandledrejection"));
        });
      } catch {
        /* @sentry/browser optional until installed */
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);
  return null;
}
