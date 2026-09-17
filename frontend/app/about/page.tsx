import type { Metadata } from "next";
import { SiteFooter } from "@/components/SiteFooter";
import { SiteHeader } from "@/components/SiteHeader";
import { ButtonLink } from "@/components/ui/Button";

export const metadata: Metadata = {
  title: "About AcademicCheck AI",
  description:
    "AcademicCheck AI is an academic success workspace: diagnose drafts against the assignment question, fix what matters, and re-check progress — without ghostwriting.",
  alternates: { canonical: "/about" },
};

export default function AboutPage() {
  return (
    <>
      <SiteHeader />
      <main id="main-content" tabIndex={-1} className="mx-auto max-w-3xl px-4 py-16 md:py-20">
        <p className="text-sm font-medium tracking-wide text-[var(--teal)]">About</p>
        <h1 className="mt-3 font-serif text-4xl md:text-5xl">Built for academic improvement — not shortcuts.</h1>
        <div className="prose-academic mt-8 space-y-5 text-[var(--ink)]">
          <p className="text-lg leading-8 text-[var(--ink-muted)]">
            AcademicCheck AI is an academic success workspace. Students upload a draft with the assignment question,
            receive a diagnostic report, fix the highest-impact issues, and re-check to see progress.
          </p>
          <p className="leading-7 text-[var(--ink-muted)]">
            We believe students deserve clarity before submission — and institutions deserve tools that respect
            academic integrity. Scores are AI-assisted diagnostic indicators, never official grades. We do not write
            assignments for submission or invent references.
          </p>
          <p className="leading-7 text-[var(--ink-muted)]">
            If you are evaluating AcademicCheck for a cohort, tutoring centre, or personal use, we are happy to talk.
          </p>
        </div>
        <div className="mt-10 flex flex-wrap gap-3">
          <ButtonLink href="/sample-report" variant="primary">
            View sample report
          </ButtonLink>
          <ButtonLink href="/contact" variant="secondary">
            Contact us
          </ButtonLink>
          <ButtonLink href="/help/academic-integrity" variant="ghost">
            Academic integrity
          </ButtonLink>
        </div>
      </main>
      <SiteFooter />
    </>
  );
}
