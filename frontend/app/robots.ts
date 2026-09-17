import type { MetadataRoute } from "next";
import { siteUrl } from "@/lib/utils";

export default function robots(): MetadataRoute.Robots {
  return {
    rules: [
      {
        userAgent: "*",
        allow: "/",
        disallow: [
          "/app/",
          "/api/",
          "/login",
          "/register",
          "/onboarding",
          "/forgot-password",
          "/reset-password",
          "/verify-email",
          "/verify",
        ],
      },
    ],
    sitemap: `${siteUrl()}/sitemap.xml`,
  };
}
