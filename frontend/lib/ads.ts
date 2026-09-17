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

function waitForGtag(ms = 4000): Promise<boolean> {
  if (typeof window === "undefined") return Promise.resolve(false);
  if (typeof window.gtag === "function") return Promise.resolve(true);
  return new Promise((resolve) => {
    const started = Date.now();
    const tick = () => {
      if (typeof window.gtag === "function") {
        resolve(true);
        return;
      }
      if (Date.now() - started >= ms) {
        resolve(false);
        return;
      }
      window.setTimeout(tick, 50);
    };
    tick();
  });
}

/**
 * Fire once per browser session after a successful new-account registration.
 * Resolves after Google's event_callback (or a short timeout) so redirects don't kill the hit.
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
    const finish = () => {
      if (done) return;
      done = true;
      try {
        sessionStorage.setItem(STORAGE_KEY, "1");
      } catch {
        /* ignore */
      }
      resolve();
    };

    window.gtag!("event", "conversion", {
      send_to: sendTo,
      value: 1.0,
      currency: "USD",
      event_callback: finish,
      event_timeout: 2000,
    });

    window.gtag!("event", "sign_up", {
      method: opts?.method || "email",
    });

    // Don't block the UX forever if callback never runs.
    window.setTimeout(finish, 2000);
  });
}

export function googleAdsConfigured() {
  return Boolean(signupSendTo());
}
