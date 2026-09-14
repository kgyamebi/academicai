export type ContentCategory =
  | "essay-writing"
  | "citations"
  | "assignment-questions"
  | "revision"
  | "integrity"
  | "product";

export type Guide = {
  slug: string;
  title: string;
  description: string;
  category: ContentCategory;
  keywords: string[];
  readingMinutes: number;
  updated: string;
  body: string;
  relatedSlugs?: string[];
};

export type BlogPost = {
  slug: string;
  title: string;
  excerpt: string;
  description: string;
  category: ContentCategory;
  keywords: string[];
  readingMinutes: number;
  published: string;
  author: string;
  body: string;
  relatedResourceSlugs?: string[];
};

export const CATEGORY_LABELS: Record<ContentCategory, string> = {
  "essay-writing": "Essay writing",
  citations: "Citations & references",
  "assignment-questions": "Assignment questions",
  revision: "Revision & feedback",
  integrity: "Academic integrity",
  product: "Using AcademicCheck",
};
