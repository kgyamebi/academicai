import Script from "next/script";

/**
 * Loads the Google tag (gtag.js) when NEXT_PUBLIC_GOOGLE_ADS_ID is set.
 * Enables Enhanced Conversions user_data on conversion events.
 */
export function GoogleAdsInit() {
  const id = (process.env.NEXT_PUBLIC_GOOGLE_ADS_ID || "").trim();
  if (!id) return null;

  return (
    <>
      <Script src={`https://www.googletagmanager.com/gtag/js?id=${id}`} strategy="afterInteractive" />
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
