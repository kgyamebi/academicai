import type { Metadata } from "next";
import Link from "next/link";
import { HeroLiveDemo } from "@/components/HeroLiveDemo";
import { SiteFooter } from "@/components/SiteFooter";
import { SiteHeader } from "@/components/SiteHeader";
import { ButtonLink } from "@/components/ui/Button";
import { messages } from "@/lib/i18n";
import { siteUrl } from "@/lib/utils";

const HOME_TITLE = "Free Assignment, Thesis & Citation Checker | AcademicCheck AI";
const HOME_DESCRIPTION =
  "Get actionable feedback on your assignment’s thesis, argument, evidence, structure and citations before submission. Free first check.";

export const metadata: Metadata = {
  title: { absolute: HOME_TITLE },
  description: HOME_DESCRIPTION,
  alternates: { canonical: "/" },
  openGraph: {
    title: HOME_TITLE,
    description: HOME_DESCRIPTION,
    url: "/",
    type: "website",
  },
};

export default function HomePage() {
  const jsonLd = {
    "@context": "https://schema.org",
    "@graph": [
      {
        "@type": "WebSite",
        name: "AcademicCheck AI",
        url: siteUrl(),
        description: HOME_DESCRIPTION,
      },
      {
        "@type": "SoftwareApplication",
        name: "AcademicCheck AI",
        applicationCategory: "EducationalApplication",
        operatingSystem: "Web",
        url: siteUrl(),
        description: HOME_DESCRIPTION,
        offers: { "@type": "Offer", price: "0", priceCurrency: "USD" },
      },
    ],
  };

  return (
    <>
      <SiteHeader />
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }} />
      <main id="main-content" tabIndex={-1}>
        <section className="ac-hero-plane relative overflow-hidden">
          <div className="ac-hero-grid pointer-events-none absolute inset-0" aria-hidden />
          <div className="relative mx-auto grid max-w-6xl gap-12 px-4 py-16 md:grid-cols-[1.05fr_0.95fr] md:items-center md:py-24">
            <div>
              <p className="font-serif text-4xl tracking-tight text-[var(--ink)] md:text-6xl">
                AcademicCheck <span className="text-[var(--teal)]">AI</span>
              </p>
              <h1 className="mt-5 max-w-xl font-serif text-3xl leading-tight text-[var(--ink)] md:text-5xl">
                {messages.heroTitle}
              </h1>
              <p className="mt-5 max-w-lg text-lg leading-8 text-[var(--ink-muted)]">{messages.heroSub}</p>
              <p className="mt-3 max-w-lg text-sm leading-6 text-[var(--ink)]">
                Your lecturer grades against the question. So do we.
              </p>
              <div className="mt-8 flex flex-col gap-3 sm:flex-row sm:items-center">
                <ButtonLink href="/check" variant="primary" className="px-6 text-base">
                  {messages.primaryCta}
                </ButtonLink>
                <ButtonLink href="/sample-report" variant="secondary" className="px-6 text-base">
                  View sample report
                </ButtonLink>
              </div>
              <p className="mt-6 text-xs leading-5 text-[var(--ink-muted)]">{messages.disclaimer}</p>
            </div>

            <aside className="relative" aria-label="Live demonstration of AcademicCheck diagnostics">
              <HeroLiveDemo />
            </aside>
          </div>
        </section>

        {/* SEE WHAT STUDENTS RECEIVE */}
        <section id="see-output" className="border-t border-[var(--rule)] bg-[var(--paper-2)]">
          <div className="mx-auto max-w-6xl px-4 py-20">
            <p className="text-sm font-medium tracking-wide text-[var(--teal)]">Output</p>
            <h2 className="mt-3 max-w-2xl font-serif text-3xl md:text-4xl">See what students receive</h2>
            <p className="mt-4 max-w-2xl text-[var(--ink-muted)] leading-7">
              Not features. Not models. A clear diagnosis you can act on before submission.
            </p>
            <ul className="mt-12 grid gap-6 md:grid-cols-3">
              {[
                ["Academic Health Score", "One number that summarises readiness — explicitly not an official grade."],
                ["Top 3 Fix-First", "Highest-impact issues with time and expected lift, so you know what to do next."],
                ["Improvement opportunity", "Before/after preview so revision effort feels concrete, not vague."],
              ].map(([title, body]) => (
                <li key={title} className="border-t border-[var(--rule)] pt-5">
                  <h3 className="font-serif text-xl">{title}</h3>
                  <p className="mt-2 text-sm leading-7 text-[var(--ink-muted)]">{body}</p>
                </li>
              ))}
            </ul>
          </div>
        </section>

        {/* HOW IT WORKS */}
        <section id="how-it-works" className="mx-auto max-w-6xl px-4 py-20">
          <p className="text-sm font-medium tracking-wide text-[var(--teal)]">How AcademicCheck works</p>
          <h2 className="mt-3 max-w-xl font-serif text-3xl md:text-4xl">From draft anxiety to a clear next step.</h2>
          <ol className="mt-12 grid gap-10 md:grid-cols-4">
            {[
              ["01", "Upload draft", "Paste text or drop DOCX/PDF with the assignment question."],
              ["02", "Receive analysis", "Relevance, thesis, argument, evidence, structure, writing, citations."],
              ["03", "Fix highest impact", "Start with Fix-First — then re-check to see progress."],
              ["04", "Submit with confidence", "Know what is strong, what is weak, and what still needs work."],
            ].map(([n, title, body]) => (
              <li key={n}>
                <p className="font-serif text-3xl text-[var(--teal)]">{n}</p>
                <h3 className="mt-3 font-serif text-xl">{title}</h3>
                <p className="mt-2 text-sm leading-7 text-[var(--ink-muted)]">{body}</p>
              </li>
            ))}
          </ol>
        </section>

        {/* INTEGRITY + PRIVACY */}
        <section className="border-t border-[var(--rule)] bg-[var(--paper-2)]">
          <div className="mx-auto grid max-w-6xl gap-10 px-4 py-20 md:grid-cols-2">
            <div>
              <p className="text-sm font-medium tracking-wide text-[var(--teal)]">Academic Integrity Promise</p>
              <h2 className="mt-3 font-serif text-2xl md:text-3xl">We help you improve your work — we do not write it.</h2>
              <ul className="mt-6 space-y-3 text-sm leading-7 text-[var(--ink)]">
                <li>AcademicCheck helps improve work.</li>
                <li>It does not write assignments for submission.</li>
                <li>It does not guarantee grades.</li>
                <li>It does not generate fake references.</li>
              </ul>
            </div>
            <div>
              <p className="text-sm font-medium tracking-wide text-[var(--teal)]">Data Privacy Promise</p>
              <h2 className="mt-3 font-serif text-2xl md:text-3xl">Your draft is coursework — we treat it that way.</h2>
              <p className="mt-6 text-sm leading-7 text-[var(--ink-muted)]">
                We use your documents to run the analysis you asked for. We do not sell your essays. Training on your
                work only happens if you explicitly opt in. You can delete your account and associated data from
                Settings. Guest checks are temporary.
              </p>
              <div className="mt-6 flex flex-wrap gap-4 text-sm">
                <Link href="/help/privacy" className="font-medium text-[var(--teal)] underline-offset-4 hover:underline">
                  Privacy details
                </Link>
                <Link href="/about" className="font-medium text-[var(--teal)] underline-offset-4 hover:underline">
                  About us
                </Link>
                <Link href="/contact" className="font-medium text-[var(--teal)] underline-offset-4 hover:underline">
                  Contact
                </Link>
              </div>
            </div>
          </div>
        </section>

        <section className="mx-auto max-w-6xl px-4 py-16">
          <div className="flex flex-col items-start justify-between gap-6 rounded-[var(--radius-lg)] border border-[var(--rule)] bg-[var(--paper-2)] p-8 md:flex-row md:items-center">
            <div>
              <h2 className="font-serif text-2xl md:text-3xl">Ready for a clear next step?</h2>
              <p className="mt-2 text-sm text-[var(--ink-muted)]">First check available without an account.</p>
            </div>
            <ButtonLink href="/check" variant="primary" className="px-6">
              Check my assignment
            </ButtonLink>
          </div>
        </section>
      </main>
      <SiteFooter />
    </>
  );
}
