import type { MetadataRoute } from "next";
import { siteUrl } from "@/lib/utils";

const slugs = [
  "",
  "pricing",
  "features",
  "blog",
  "help",
  "check",
  "ai-essay-checker",
  "assignment-checker",
  "essay-checker",
  "academic-writing-checker",
  "citation-checker",
  "thesis-checker",
  "essay-checker-ghana",
  "assignment-checker-nigeria",
];

export default function sitemap(): MetadataRoute.Sitemap {
  const base = siteUrl();
  return slugs.map((slug) => ({
    url: slug ? `${base}/${slug}` : base,
    changeFrequency: "weekly",
    priority: slug ? 0.7 : 1,
  }));
}
