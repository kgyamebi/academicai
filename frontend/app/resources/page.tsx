import type { Metadata } from "next";
import Link from "next/link";
import { SiteFooter } from "@/components/SiteFooter";
import { SiteHeader } from "@/components/SiteHeader";
import { ContentCta } from "@/components/content/GuideBody";
import { CATEGORY_LABELS } from "@/lib/content/types";
import { RESOURCES, resourcesByCategory } from "@/lib/content/resources";
import { siteUrl } from "@/lib/utils";

export const metadata: Metadata = {
  title: "Resources centre — essay, citation & assignment guides",
  description:
    "Free student resources: essay structure, command words, APA/MLA/Harvard citations, revision checklists, and academic integrity — built to help you improve before submission.",
  keywords: [
    "essay writing guides",
    "assignment resources",
    "APA citation guide",
    "critically discuss meaning",
    "university essay structure",
  ],
  alternates: { canonical: "/resources" },
  openGraph: {
    title: "AcademicCheck Resources centre",
    description: "Practical guides for university essays, citations, and revision.",
    type: "website",
  },
};

export default function ResourcesHubPage() {
  const grouped = resourcesByCategory();
  const jsonLd = {
    "@context": "https://schema.org",
    "@type": "CollectionPage",
    name: "AcademicCheck Resources centre",
    description: "Student guides for essays, citations, and assignment revision.",
    hasPart: RESOURCES.map((g) => ({
      "@type": "TechArticle",
      headline: g.title,
      description: g.description,
      url: `${siteUrl()}/resources/${g.slug}`,
    })),
  };

  return (
    <>
      <SiteHeader />
      <main id="main-content" tabIndex={-1}>
        <section className="border-b border-[var(--rule)] bg-[var(--paper-2)]">
          <div className="mx-auto max-w-6xl px-4 py-16 md:py-20">
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-[var(--teal)]">Resources</p>
            <h1 className="mt-3 max-w-3xl font-serif text-4xl leading-tight md:text-5xl">
              Student resources that improve the draft you already wrote
            </h1>
            <p className="mt-4 max-w-2xl text-base leading-7 text-[var(--ink-muted)]">
              Practical guides on essay structure, command words, citations, and revision — plus how to use AcademicCheck
              as a diagnostic study aid, not a ghostwriter.
            </p>
            <p className="mt-4 text-sm text-[var(--ink-muted)]">{RESOURCES.length} guides · free to read</p>
          </div>
        </section>

        <div className="mx-auto max-w-6xl px-4 py-14">
          <div className="grid gap-12 lg:grid-cols-[220px_1fr]">
            <nav aria-label="Resource categories" className="lg:sticky lg:top-24 lg:self-start">
              <p className="text-sm font-semibold">Browse</p>
              <ul className="mt-3 space-y-2 text-sm text-[var(--ink-muted)]">
                {Object.keys(grouped).map((cat) => (
                  <li key={cat}>
                    <a href={`#${cat}`} className="hover:text-[var(--ink)]">
                      {CATEGORY_LABELS[cat as keyof typeof CATEGORY_LABELS]}
                    </a>
                  </li>
                ))}
                <li className="pt-2">
                  <Link href="/blog" className="text-[var(--teal)] hover:underline">
                    Writing blog →
                  </Link>
                </li>
                <li>
                  <Link href="/help" className="text-[var(--teal)] hover:underline">
                    Help centre →
                  </Link>
                </li>
              </ul>
            </nav>

            <div className="space-y-14">
              {Object.entries(grouped).map(([cat, items]) => (
                <section key={cat} id={cat} aria-labelledby={`h-${cat}`}>
                  <h2 id={`h-${cat}`} className="font-serif text-3xl">
                    {CATEGORY_LABELS[cat as keyof typeof CATEGORY_LABELS]}
                  </h2>
                  <ul className="mt-6 divide-y divide-[var(--rule)] border-y border-[var(--rule)]">
                    {items.map((g) => (
                      <li key={g.slug} className="py-5">
                        <Link href={`/resources/${g.slug}`} className="group block">
                          <h3 className="font-serif text-xl text-[var(--ink)] group-hover:text-[var(--teal)]">
                            {g.title}
                          </h3>
                          <p className="mt-1 text-sm leading-6 text-[var(--ink-muted)]">{g.description}</p>
                          <p className="mt-2 text-xs text-[var(--ink-muted)]">{g.readingMinutes} min read</p>
                        </Link>
                      </li>
                    ))}
                  </ul>
                </section>
              ))}
            </div>
          </div>

          <ContentCta />
        </div>
      </main>
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }} />
      <SiteFooter />
    </>
  );
}
