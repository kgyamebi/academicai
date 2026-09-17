import type { MetadataRoute } from "next";
import { allBlogSlugs } from "@/lib/content/blog";
import { allResourceSlugs } from "@/lib/content/resources";
import { checkerLandingPages } from "@/lib/checkerLandingPages";
import { siteUrl } from "@/lib/utils";

const core = [
  "",
  "pricing",
  "features",
  "blog",
  "resources",
  "help",
  "check",
  "about",
  "contact",
  "security",
  "terms",
  "sample-report",
];

const helpTopics = [
  "help/how-to-check",
  "help/file-types",
  "help/citation-styles",
  "help/ai-writing-indicators",
  "help/rubric-checker",
  "help/privacy",
  "help/pricing",
  "help/academic-integrity",
];

export default function sitemap(): MetadataRoute.Sitemap {
  const base = siteUrl();
  const moneySlugs = Object.keys(checkerLandingPages);
  const prioritySlugs = new Set(["assignment-checker", "thesis-checker", "citation-checker"]);
  const staticPaths = [
    ...core,
    ...moneySlugs,
    ...helpTopics,
    ...allResourceSlugs().map((s) => `resources/${s}`),
    ...allBlogSlugs().map((s) => `blog/${s}`),
  ];
  return staticPaths.map((slug) => ({
    url: slug ? `${base}/${slug}` : base,
    changeFrequency: slug.startsWith("blog/") || slug.startsWith("resources/") ? "monthly" : "weekly",
    priority: !slug
      ? 1
      : prioritySlugs.has(slug) || slug === "resources" || slug === "blog"
        ? 0.9
        : slug.startsWith("resources/") || slug.startsWith("blog/")
          ? 0.8
          : 0.7,
  }));
}
