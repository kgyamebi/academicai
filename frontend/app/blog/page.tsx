import type { Metadata } from "next";
import Link from "next/link";
import { SiteFooter } from "@/components/SiteFooter";
import { SiteHeader } from "@/components/SiteHeader";
import { ContentCta } from "@/components/content/GuideBody";
import { blogPostsSorted } from "@/lib/content/blog";
import { CATEGORY_LABELS } from "@/lib/content/types";
import { apiUrl } from "@/lib/utils";

export const metadata: Metadata = {
  title: "Writing guides blog",
  description:
    "University writing guides: essay structure, critically discuss, APA citations, revision checklists, and how to use AcademicCheck reports.",
  keywords: ["university writing blog", "essay writing tips", "critically discuss", "APA citation"],
  alternates: { canonical: "/blog" },
  openGraph: {
    title: "AcademicCheck writing guides",
    description: "Practical blog posts for coursework essays and assignment revision.",
    type: "website",
  },
};

type ApiItem = { slug: string; title: string; excerpt: string; published_at?: string | null };

async function loadApiPosts(): Promise<ApiItem[]> {
  try {
    const res = await fetch(`${apiUrl()}/api/public/blog`, { next: { revalidate: 300 } });
    if (!res.ok) return [];
    const data = await res.json();
    return Array.isArray(data.items) ? data.items : [];
  } catch {
    return [];
  }
}

export default async function BlogIndex() {
  const staticPosts = blogPostsSorted();
  const apiPosts = await loadApiPosts();
  const staticSlugs = new Set(staticPosts.map((p) => p.slug));
  const extras = apiPosts.filter((p) => !staticSlugs.has(p.slug));

  const jsonLd = {
    "@context": "https://schema.org",
    "@type": "Blog",
    name: "AcademicCheck writing guides",
    blogPost: staticPosts.map((p) => ({
      "@type": "BlogPosting",
      headline: p.title,
      description: p.excerpt,
      datePublished: p.published,
      author: { "@type": "Person", name: p.author },
    })),
  };

  return (
    <>
      <SiteHeader />
      <main id="main-content" tabIndex={-1}>
        <section className="border-b border-[var(--rule)] bg-[var(--paper-2)]">
          <div className="mx-auto max-w-3xl px-4 py-16">
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-[var(--teal)]">Blog</p>
            <h1 className="mt-3 font-serif text-4xl md:text-5xl">Writing guides</h1>
            <p className="mt-4 text-base leading-7 text-[var(--ink-muted)]">
              Short, searchable posts on structure, command words, citations, and revision — linked into our{" "}
              <Link href="/resources" className="text-[var(--teal)] underline-offset-4 hover:underline">
                Resources centre
              </Link>
              .
            </p>
          </div>
        </section>

        <div className="mx-auto max-w-3xl px-4 py-12">
          <ul className="divide-y divide-[var(--rule)] border-y border-[var(--rule)]">
            {staticPosts.map((p) => (
              <li key={p.slug} className="py-7">
                <p className="text-xs uppercase tracking-wide text-[var(--ink-muted)]">
                  {CATEGORY_LABELS[p.category]} · {p.readingMinutes} min · {p.published}
                </p>
                <Link href={`/blog/${p.slug}`} className="mt-2 block font-serif text-2xl hover:text-[var(--teal)]">
                  {p.title}
                </Link>
                <p className="mt-2 text-sm leading-6 text-[var(--ink-muted)]">{p.excerpt}</p>
              </li>
            ))}
            {extras.map((p) => (
              <li key={p.slug} className="py-7">
                <Link href={`/blog/${p.slug}`} className="font-serif text-2xl hover:text-[var(--teal)]">
                  {p.title}
                </Link>
                <p className="mt-2 text-sm text-[var(--ink-muted)]">{p.excerpt}</p>
              </li>
            ))}
          </ul>
          <ContentCta title="Put a guide into practice" />
        </div>
      </main>
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }} />
      <SiteFooter />
    </>
  );
}
