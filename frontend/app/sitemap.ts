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
  "about",
  "contact",
  "security",
  "terms",
  "sample-report",
  "login",
  "register",
];

export default function sitemap(): MetadataRoute.Sitemap {
  const base = siteUrl();
  return slugs.map((slug) => ({
    url: slug ? `${base}/${slug}` : base,
    changeFrequency: "weekly",
    priority: slug ? 0.7 : 1,
  }));
}
