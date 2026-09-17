/**
 * Google Ads conversion helpers.
 * Requires NEXT_PUBLIC_GOOGLE_ADS_ID (e.g. AW-7774862177) and
 * NEXT_PUBLIC_GOOGLE_ADS_SIGNUP_LABEL (from Ads → Sign-up → Tag setup → Event snippet).
 */

declare global {
  interface Window {
    dataLayer?: unknown[];
    gtag?: (...args: unknown[]) => void;
    __AC_GTAG_READY?: boolean;
  }
}

const STORAGE_KEY = "ac_ads_signup_sent";

function adsId() {
  return (process.env.NEXT_PUBLIC_GOOGLE_ADS_ID || "").trim();
}

function signupSendTo() {
  const id = adsId();
  const label = (process.env.NEXT_PUBLIC_GOOGLE_ADS_SIGNUP_LABEL || "").trim();
  if (!id || !label) return "";
  return `${id}/${label}`;
}

/** Wait until the real googletagmanager script has loaded — not just the inline stub. */
function waitForGtag(ms = 8000): Promise<boolean> {
  if (typeof window === "undefined") return Promise.resolve(false);
  if (window.__AC_GTAG_READY && typeof window.gtag === "function") return Promise.resolve(true);
  return new Promise((resolve) => {
    const started = Date.now();
    const tick = () => {
      if (window.__AC_GTAG_READY && typeof window.gtag === "function") {
        resolve(true);
        return;
      }
      // Fallback: script element finished loading even if onLoad missed
      const el = document.querySelector('script[src*="googletagmanager.com/gtag/js"]') as HTMLScriptElement | null;
      if (el && typeof window.gtag === "function") {
        const loaded = el.getAttribute("data-nscript") || el.getAttribute("src");
        if (loaded && (el as HTMLScriptElement & { dataset?: DOMStringMap }).dataset) {
          /* continue */
        }
        // If transfer already happened, treat as ready after a short settle
        const entries = performance.getEntriesByName(el.src, "resource") as PerformanceResourceTiming[];
        if (entries.some((e) => e.transferSize > 0 || e.responseStatus === 200)) {
          window.__AC_GTAG_READY = true;
          resolve(true);
          return;
        }
      }
      if (Date.now() - started >= ms) {
        resolve(Boolean(window.__AC_GTAG_READY && typeof window.gtag === "function"));
        return;
      }
      window.setTimeout(tick, 50);
    };
    tick();
  });
}

/**
 * Fire once per browser session after a successful new-account registration.
 * Only marks the session as sent when Google's event_callback runs (real delivery).
 */
export async function trackAdsSignup(opts?: { email?: string | null; method?: string }): Promise<void> {
  if (typeof window === "undefined") return;
  const sendTo = signupSendTo();
  if (!sendTo) return;

  try {
    if (sessionStorage.getItem(STORAGE_KEY) === "1") return;
  } catch {
    /* private mode */
  }

  const ready = await waitForGtag();
  if (!ready || typeof window.gtag !== "function") return;

  const email = (opts?.email || "").trim().toLowerCase();
  if (email) {
    window.gtag("set", "user_data", { email });
  }

  await new Promise<void>((resolve) => {
    let done = false;
    const finish = (markSent: boolean) => {
      if (done) return;
      done = true;
      if (markSent) {
        try {
          sessionStorage.setItem(STORAGE_KEY, "1");
        } catch {
          /* ignore */
        }
      }
      resolve();
    };

    window.gtag!("event", "conversion", {
      send_to: sendTo,
      value: 1.0,
      currency: "USD",
      event_callback: () => finish(true),
      event_timeout: 5000,
    });

    window.gtag!("event", "sign_up", {
      method: opts?.method || "email",
    });

    // Do NOT mark sent on timeout — allow onboarding beacon to retry.
    window.setTimeout(() => finish(false), 5000);
  });
}

export function googleAdsConfigured() {
  return Boolean(signupSendTo());
}
