/**
 * Google Ads conversion helpers.
 * Requires NEXT_PUBLIC_GOOGLE_ADS_ID (e.g. AW-7774862177) and
 * NEXT_PUBLIC_GOOGLE_ADS_SIGNUP_LABEL (from Ads → Sign-up → Tag setup → Event snippet).
 */

declare global {
  interface Window {
    dataLayer?: unknown[];
    gtag?: (...args: unknown[]) => void;
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

/** Fire once per browser session after a successful new-account registration. */
export function trackAdsSignup(opts?: { email?: string | null; method?: string }) {
  if (typeof window === "undefined") return;
  const sendTo = signupSendTo();
  if (!sendTo || typeof window.gtag !== "function") return;

  try {
    if (sessionStorage.getItem(STORAGE_KEY) === "1") return;
    sessionStorage.setItem(STORAGE_KEY, "1");
  } catch {
    /* private mode — still attempt one fire */
  }

  const email = (opts?.email || "").trim().toLowerCase();
  if (email) {
    window.gtag("set", "user_data", { email });
  }

  window.gtag("event", "conversion", {
    send_to: sendTo,
    value: 1.0,
    currency: "USD",
  });

  window.gtag("event", "sign_up", {
    method: opts?.method || "email",
  });
}

export function googleAdsConfigured() {
  return Boolean(signupSendTo());
}
