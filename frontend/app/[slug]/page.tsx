import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { SiteFooter } from "@/components/SiteFooter";
import { SiteHeader } from "@/components/SiteHeader";
import { ButtonLink } from "@/components/ui/Button";
import { checkerLandingPages, type CheckerLandingPage } from "@/lib/checkerLandingPages";
import { apiUrl, siteUrl } from "@/lib/utils";

export function generateStaticParams() {
  return Object.keys(checkerLandingPages).map((slug) => ({ slug }));
}

async function loadPage(slug: string) {
  const res = await fetch(`${apiUrl()}/api/public/seo/${slug}`, { next: { revalidate: 300 } });
  if (!res.ok) return null;
  return res.json() as Promise<{
    title: string;
    meta_description: string;
    heading: string;
    body_markdown: string;
    canonical_path: string;
  }>;
}

export async function generateMetadata({ params }: { params: Promise<{ slug: string }> }): Promise<Metadata> {
  const { slug } = await params;
  const page = await loadPage(slug);
  if (page) {
    const canonical = page.canonical_path.startsWith("http")
      ? page.canonical_path
      : `${siteUrl()}${page.canonical_path.startsWith("/") ? "" : "/"}${page.canonical_path}`;
    return {
      title: page.title,
      description: page.meta_description,
      alternates: { canonical },
      openGraph: {
        title: page.heading,
        description: page.meta_description,
        url: canonical,
        type: "website",
      },
    };
  }
  const fallback = checkerLandingPages[slug];
  if (fallback) {
    const canonical = `${siteUrl()}/${slug}`;
    return {
      title: { absolute: fallback.title },
      description: fallback.description,
      alternates: { canonical },
      openGraph: {
        title: fallback.heading,
        description: fallback.description,
        url: canonical,
        type: "website",
      },
    };
  }
  return {};
}

export default async function SeoPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const reserved = new Set([
    "app",
    "check",
    "login",
    "register",
    "pricing",
    "features",
    "blog",
    "help",
    "resources",
    "shared",
    "verify",
    "verify-email",
    "forgot-password",
    "reset-password",
    "about",
    "contact",
    "security",
    "terms",
    "sample-report",
    "onboarding",
  ]);
  if (reserved.has(slug)) notFound();
  const page = await loadPage(slug);
  if (!page) {
    const fallback = checkerLandingPages[slug];
    if (fallback) return <CheckerMoneyPage slug={slug} page={fallback} />;
    notFound();
  }
  return (
    <>
      <SiteHeader />
      <main id="main-content" tabIndex={-1} className="prose-academic mx-auto max-w-3xl px-4 py-16">
        <article className="whitespace-pre-wrap leading-7">{page.body_markdown}</article>
        <p className="mt-10 text-sm text-[var(--ink-muted)]">
          AI-assisted feedback is not an official grade. Always follow your institution’s academic-integrity policies.
        </p>
      </main>
      <SiteFooter />
    </>
  );
}

function CheckerMoneyPage({ slug, page }: { slug: string; page: CheckerLandingPage }) {
  const canonical = `${siteUrl()}/${slug}`;
  const structuredData = {
    "@context": "https://schema.org",
    "@graph": [
      {
        "@type": "WebPage",
        name: page.heading,
        description: page.description,
        url: canonical,
        isPartOf: { "@type": "WebSite", name: "AcademicCheck AI", url: siteUrl() },
      },
      {
        "@type": "SoftwareApplication",
        name: "AcademicCheck AI",
        applicationCategory: "EducationalApplication",
        operatingSystem: "Web",
        url: siteUrl(),
        description: page.description,
        offers: { "@type": "Offer", price: "0", priceCurrency: "USD" },
      },
      {
        "@type": "FAQPage",
        mainEntity: page.faqs.map((faq) => ({
          "@type": "Question",
          name: faq.question,
          acceptedAnswer: { "@type": "Answer", text: faq.answer },
        })),
      },
    ],
  };

  return (
    <>
      <SiteHeader />
      <main id="main-content" tabIndex={-1}>
        <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(structuredData) }} />

        <section className="border-b border-[var(--rule)] bg-[var(--paper)]">
          <div className="mx-auto max-w-3xl px-4 py-16 md:py-20">
            <p className="text-sm font-medium uppercase tracking-[0.16em] text-[var(--teal)]">{page.eyebrow}</p>
            <h1 className="mt-4 font-serif text-4xl leading-tight md:text-5xl">{page.heading}</h1>
            <p className="mt-6 text-lg leading-8 text-[var(--ink-muted)]">{page.intro}</p>
            <div className="mt-8 flex flex-col gap-3 sm:flex-row sm:items-center">
              <ButtonLink href="/check" variant="primary" className="px-6 text-base">
                {page.cta}
              </ButtonLink>
              <ButtonLink href="/sample-report" variant="secondary" className="px-6 text-base">
                View sample report
              </ButtonLink>
            </div>
          </div>
        </section>

        <section className="mx-auto max-w-3xl px-4 py-14">
          <h2 className="font-serif text-3xl">What this checker reviews</h2>
          <ul className="mt-5 list-disc space-y-3 pl-6 leading-7 text-[var(--ink)]">
            {page.checks.map((check) => (
              <li key={check}>{check}</li>
            ))}
          </ul>
        </section>

        <section className="border-y border-[var(--rule)] bg-[var(--paper-2)]">
          <div className="mx-auto max-w-3xl px-4 py-14">
            <p className="text-sm font-medium tracking-wide text-[var(--teal)]">Sample result</p>
            <h2 className="mt-2 font-serif text-3xl">What feedback can look like</h2>
            <p className="mt-3 text-sm leading-7 text-[var(--ink-muted)]">
              Illustrative preview—not a live grade. Your report will reflect your draft.
            </p>
            <div className="mt-8 border border-[var(--rule)] bg-[var(--paper)] p-6">
              <div className="flex flex-wrap items-end gap-6">
                <div>
                  <p className="text-xs uppercase tracking-wide text-[var(--ink-muted)]">Academic Health Score</p>
                  <p className="mt-1 font-serif text-4xl tabular-nums">{page.sample.score}</p>
                </div>
                <p className="font-medium text-[var(--teal)]">{page.sample.readiness}</p>
              </div>
              <ol className="mt-6 space-y-4 border-t border-[var(--rule)] pt-5">
                {page.sample.findings.map((finding, i) => (
                  <li key={finding.title}>
                    <p className="font-serif text-lg">
                      <span className="text-[var(--teal)]">{String(i + 1).padStart(2, "0")}</span> {finding.title}
                    </p>
                    <p className="mt-1 text-sm leading-7 text-[var(--ink-muted)]">{finding.detail}</p>
                  </li>
                ))}
              </ol>
            </div>
          </div>
        </section>

        <section className="mx-auto max-w-3xl px-4 py-14">
          <h2 className="font-serif text-3xl">How it works</h2>
          <ol className="mt-8 grid gap-8 sm:grid-cols-3">
            {page.howItWorks.map((item) => (
              <li key={item.step}>
                <p className="font-serif text-3xl text-[var(--teal)]">{item.step}</p>
                <h3 className="mt-2 font-serif text-xl">{item.title}</h3>
                <p className="mt-2 text-sm leading-7 text-[var(--ink-muted)]">{item.body}</p>
              </li>
            ))}
          </ol>
          <div className="mt-10">
            <ButtonLink href="/check" variant="primary" className="px-6">
              {page.cta}
            </ButtonLink>
          </div>
        </section>

        {page.sections.map((section) => (
          <section key={section.heading} className="mx-auto max-w-3xl px-4 py-10">
            <h2 className="font-serif text-3xl">{section.heading}</h2>
            {section.paragraphs.map((paragraph) => (
              <p key={paragraph.slice(0, 48)} className="mt-4 leading-8 text-[var(--ink)]">
                {paragraph}
              </p>
            ))}
          </section>
        ))}

        <section className="border-t border-[var(--rule)] bg-[var(--paper-2)]">
          <div className="mx-auto max-w-3xl px-4 py-14">
            <h2 className="font-serif text-3xl">Frequently asked questions</h2>
            <div className="mt-8 space-y-8">
              {page.faqs.map((faq) => (
                <section key={faq.question}>
                  <h3 className="font-serif text-xl">{faq.question}</h3>
                  <p className="mt-2 leading-7 text-[var(--ink-muted)]">{faq.answer}</p>
                </section>
              ))}
            </div>
          </div>
        </section>

        <section className="mx-auto max-w-3xl px-4 py-14">
          <h2 className="font-serif text-2xl">Keep exploring</h2>
          <ul className="mt-4 space-y-2 text-sm">
            {page.related.map((item) => (
              <li key={item.href}>
                <Link href={item.href} className="text-[var(--teal)] underline-offset-4 hover:underline">
                  {item.label}
                </Link>
              </li>
            ))}
          </ul>
          <p className="mt-10 text-sm leading-6 text-[var(--ink-muted)]">
            AI-assisted feedback is not an official grade. Citation checks do not prove a source is real. Always follow
            your institution’s academic-integrity policies.{" "}
            <Link href="/help/academic-integrity" className="underline-offset-4 hover:underline">
              Integrity guidance
            </Link>
            .
          </p>
        </section>
      </main>
      <SiteFooter />
    </>
  );
}
