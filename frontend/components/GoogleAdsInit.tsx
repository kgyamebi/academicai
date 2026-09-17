"use client";

import Script from "next/script";

declare global {
  interface Window {
    __AC_GTAG_READY?: boolean;
  }
}

/**
 * Loads the Google tag (gtag.js) when NEXT_PUBLIC_GOOGLE_ADS_ID is set.
 * Sets window.__AC_GTAG_READY only after the real googletagmanager script loads
 * (the inline stub alone is not enough to send conversions).
 */
export function GoogleAdsInit() {
  const id = (process.env.NEXT_PUBLIC_GOOGLE_ADS_ID || "").trim();
  if (!id) return null;

  return (
    <>
      <Script
        src={`https://www.googletagmanager.com/gtag/js?id=${id}`}
        strategy="afterInteractive"
        onLoad={() => {
          if (typeof window !== "undefined") window.__AC_GTAG_READY = true;
        }}
      />
      <Script id="google-ads-init" strategy="afterInteractive">
        {`
          window.dataLayer = window.dataLayer || [];
          function gtag(){dataLayer.push(arguments);}
          gtag('js', new Date());
          gtag('config', '${id}', { allow_enhanced_conversions: true });
        `}
      </Script>
    </>
  );
}
