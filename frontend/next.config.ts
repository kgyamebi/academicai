import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  poweredByHeader: false,
  devIndicators: false,
  async rewrites() {
    // Always proxy to the in-process/local API — never loop through the public domain.
    const api = process.env.API_INTERNAL_URL || "http://127.0.0.1:8000";
    return [{ source: "/api/:path*", destination: `${api}/api/:path*` }];
  },
  async headers() {
    return [
      {
        source: "/(.*)",
        headers: [
          { key: "X-Content-Type-Options", value: "nosniff" },
          { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
          { key: "X-Frame-Options", value: "DENY" },
          { key: "Permissions-Policy", value: "camera=(), microphone=(), geolocation=()" },
          {
            key: "Content-Security-Policy",
            // Google Ads / gtag measurement — must include Analytics + Ads endpoints or
            // Ads Tag diagnostics reports "CSP blocking measurement".
            value: [
              "default-src 'self'",
              [
                "script-src 'self' 'unsafe-inline' 'unsafe-eval'",
                "https://www.googletagmanager.com",
                "https://*.googletagmanager.com",
                "https://www.googleadservices.com",
                "https://www.google.com",
                "https://pagead2.googlesyndication.com",
                "https://googleads.g.doubleclick.net",
              ].join(" "),
              // Ads Tag diagnostics checks script-src-elem explicitly (not only script-src).
              [
                "script-src-elem 'self' 'unsafe-inline'",
                "https://www.googletagmanager.com",
                "https://*.googletagmanager.com",
                "https://www.googleadservices.com",
                "https://www.google.com",
                "https://pagead2.googlesyndication.com",
                "https://googleads.g.doubleclick.net",
              ].join(" "),
              "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
              "font-src 'self' https://fonts.gstatic.com data:",
              [
                "img-src 'self' data: blob:",
                "https://www.googletagmanager.com",
                "https://*.googletagmanager.com",
                "https://www.google.com",
                "https://*.google.com",
                "https://google.com",
                "https://www.googleadservices.com",
                "https://pagead2.googlesyndication.com",
                "https://googleads.g.doubleclick.net",
                "https://*.g.doubleclick.net",
                "https://ad.doubleclick.net",
                "https://www.google-analytics.com",
                "https://*.google-analytics.com",
                "https://www.google.co.uk",
              ].join(" "),
              [
                "connect-src 'self'",
                "https://www.googletagmanager.com",
                "https://*.googletagmanager.com",
                "https://www.google.com",
                "https://*.google.com",
                "https://google.com",
                "https://www.googleadservices.com",
                "https://pagead2.googlesyndication.com",
                "https://googleads.g.doubleclick.net",
                "https://*.g.doubleclick.net",
                "https://stats.g.doubleclick.net",
                "https://td.doubleclick.net",
                "https://ad.doubleclick.net",
                "https://www.google-analytics.com",
                "https://*.google-analytics.com",
                "https://*.analytics.google.com",
                "https://www.google.co.uk",
              ].join(" "),
              "frame-src https://www.googletagmanager.com https://*.googletagmanager.com https://www.google.com https://td.doubleclick.net",
              "frame-ancestors 'none'",
              "base-uri 'self'",
              "form-action 'self'",
            ].join("; "),
          },
          { key: "Strict-Transport-Security", value: "max-age=63072000; includeSubDomains; preload" },
        ],
      },
    ];
  },
};

export default nextConfig;
