import type { Metadata } from "next";
import { AmbientStage } from "@/components/AmbientStage";
import { SiteFooter } from "@/components/SiteFooter";
import { SiteHeader } from "@/components/SiteHeader";
import { ButtonLink } from "@/components/ui/Button";

export const metadata: Metadata = {
  title: "Pricing — fully free",
  description:
    "AcademicCheck AI is fully free right now. Every feature is open. Paid checkout is paused.",
  alternates: { canonical: "/pricing" },
};

/** Public free launch — paid plans are informational only; no checkout. */
export default function PricingPage() {
  return (
    <>
      <SiteHeader />
      <AmbientStage>
        <main id="main-content" tabIndex={-1} className="mx-auto max-w-3xl px-4 py-16 md:py-20">
          <p className="text-sm font-medium tracking-wide text-[var(--teal)]">Access</p>
          <h1 className="mt-3 font-serif text-4xl md:text-5xl">Fully free, for now</h1>
          <p className="mt-4 text-[var(--ink-muted)] leading-7">
            Every AcademicCheck feature is free. Full analysis, rubric feedback, coach, citations, PDF export, sharing,
            and draft comparison are open to guests and accounts. There is no checkout and no monthly check cap.
          </p>

          <article className="ac-auth-panel mt-10 rounded-[var(--radius-lg)] border border-[var(--teal)] p-6 md:p-8">
            <h2 className="font-serif text-2xl">What you get today</h2>
            <ul className="mt-4 space-y-3 text-sm leading-7 text-[var(--ink)]">
              <li>Unlimited checks against your assignment question</li>
              <li>Full analysis, rubric feedback, citations, and AI-writing indicators</li>
              <li>Coach, PDF export, sharing, and draft comparison</li>
              <li>Integrity-first feedback — not an official grade</li>
            </ul>
            <div className="mt-8">
              <ButtonLink href="/check" variant="primary" className="px-6">
                Start a free check
              </ButtonLink>
            </div>
          </article>

          <p className="mt-10 text-sm leading-7 text-[var(--ink-muted)]">
            Paid plans may return later. Until then, nothing in the product is locked behind a subscription. We will
            never charge from the frontend alone.
          </p>
          <p className="mt-4 text-sm">
            <a href="/help/pricing" className="font-medium text-[var(--teal)] underline-offset-4 hover:underline">
              Pricing FAQ
            </a>
          </p>
        </main>
      </AmbientStage>
      <SiteFooter />
    </>
  );
}
