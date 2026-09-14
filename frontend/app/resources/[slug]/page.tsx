import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { SiteFooter } from "@/components/SiteFooter";
import { SiteHeader } from "@/components/SiteHeader";
import { ContentCta, RelatedLinks, renderGuideMarkdown } from "@/components/content/GuideBody";
import { CATEGORY_LABELS } from "@/lib/content/types";
import { allResourceSlugs, getResource } from "@/lib/content/resources";
import { siteUrl } from "@/lib/utils";

type Props = { params: Promise<{ slug: string }> };

export function generateStaticParams() {
  return allResourceSlugs().map((slug) => ({ slug }));
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { slug } = await params;
  const guide = getResource(slug);
  if (!guide) return {};
  return {
    title: guide.title,
    description: guide.description,
    keywords: guide.keywords,
    alternates: { canonical: `/resources/${guide.slug}` },
    openGraph: {
      title: guide.title,
      description: guide.description,
      type: "article",
      url: `${siteUrl()}/resources/${guide.slug}`,
    },
  };
}

export default async function ResourceArticlePage({ params }: Props) {
  const { slug } = await params;
  const guide = getResource(slug);
  if (!guide) notFound();

  const related =
    guide.relatedSlugs
      ?.map((s) => getResource(s))
      .filter(Boolean)
      .map((g) => ({ href: `/resources/${g!.slug}`, label: g!.title })) ?? [];

  const jsonLd = {
    "@context": "https://schema.org",
    "@type": "TechArticle",
    headline: guide.title,
    description: guide.description,
    dateModified: guide.updated,
    author: { "@type": "Organization", name: "AcademicCheck AI" },
    keywords: guide.keywords.join(", "),
    mainEntityOfPage: `${siteUrl()}/resources/${guide.slug}`,
  };

  return (
    <>
      <SiteHeader />
      <main id="main-content" tabIndex={-1} className="mx-auto max-w-3xl px-4 py-14">
        <nav aria-label="Breadcrumb" className="text-sm text-[var(--ink-muted)]">
          <Link href="/resources" className="hover:text-[var(--ink)]">
            Resources
          </Link>
          <span aria-hidden="true"> / </span>
          <span>{CATEGORY_LABELS[guide.category]}</span>
        </nav>
        <p className="mt-6 text-xs font-semibold uppercase tracking-[0.16em] text-[var(--teal)]">
          {CATEGORY_LABELS[guide.category]}
        </p>
        <h1 className="mt-2 font-serif text-4xl leading-tight md:text-[2.75rem]">{guide.title}</h1>
        <p className="mt-4 text-base leading-7 text-[var(--ink-muted)]">{guide.description}</p>
        <p className="mt-3 text-xs text-[var(--ink-muted)]">
          {guide.readingMinutes} min read · Updated {guide.updated}
        </p>
        <article
          className="ac-guide mt-10"
          dangerouslySetInnerHTML={{ __html: renderGuideMarkdown(guide.body) }}
        />
        <RelatedLinks heading="Related resources" items={related} />
        <RelatedLinks
          heading="Keep learning"
          items={[
            { href: "/blog", label: "Writing guides blog" },
            { href: "/sample-report", label: "Sample diagnostic report" },
            { href: "/help", label: "Help centre" },
          ]}
        />
        <ContentCta />
      </main>
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }} />
      <SiteFooter />
    </>
  );
}
