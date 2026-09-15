import type { MetadataRoute } from "next";
import { allBlogSlugs } from "@/lib/content/blog";
import { allResourceSlugs } from "@/lib/content/resources";
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
  "login",
  "register",
];

const seoLanding = [
  "ai-essay-checker",
  "assignment-checker",
  "essay-checker",
  "academic-writing-checker",
  "ai-assignment-checker",
  "research-paper-checker",
  "thesis-checker",
  "dissertation-checker",
  "essay-grammar-checker",
  "academic-grammar-checker",
  "essay-structure-checker",
  "thesis-statement-checker",
  "argument-checker",
  "paragraph-checker",
  "citation-checker",
  "apa-citation-checker",
  "mla-citation-checker",
  "harvard-citation-checker",
  "grammar-checker",
  "ai-writing-checker",
  "essay-checker-ghana",
  "assignment-checker-ghana",
  "essay-checker-nigeria",
  "assignment-checker-nigeria",
  "essay-checker-kenya",
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
  const prioritySlugs = new Set(["assignment-checker", "thesis-checker", "citation-checker"]);
  const staticPaths = [
    ...core,
    ...seoLanding,
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
