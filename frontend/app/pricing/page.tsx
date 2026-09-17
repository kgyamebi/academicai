import type { Metadata } from "next";
import { AmbientStage } from "@/components/AmbientStage";
import { SiteFooter } from "@/components/SiteFooter";
import { SiteHeader } from "@/components/SiteHeader";
import { ButtonLink } from "@/components/ui/Button";

export const metadata: Metadata = {
  title: "Pricing — free public launch",
  description:
    "AcademicCheck AI is free for students during the public launch. Fair-use limits apply; paid checkout is paused.",
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
          <h1 className="mt-3 font-serif text-4xl md:text-5xl">Free public launch</h1>
          <p className="mt-4 text-[var(--ink-muted)] leading-7">
            AcademicCheck AI is launching free for students. Paid plans are paused — there is no checkout and no
            subscription flow in this release. Limits may apply so the service stays reliable for everyone.
          </p>

          <article className="ac-auth-panel mt-10 rounded-[var(--radius-lg)] border border-[var(--teal)] p-6 md:p-8">
            <h2 className="font-serif text-2xl">What you get today</h2>
            <ul className="mt-4 space-y-3 text-sm leading-7 text-[var(--ink)]">
              <li>Guest and registered checks against your assignment question</li>
              <li>Academic Performance Overview with Top 3 Critical Fixes</li>
              <li>Dashboard progress, coach guidance, and PDF download where enabled</li>
              <li>Integrity-first feedback — not an official grade</li>
            </ul>
            <div className="mt-8">
              <ButtonLink href="/check" variant="primary" className="px-6">
                Start a free check
              </ButtonLink>
            </div>
          </article>

          <p className="mt-10 text-sm leading-7 text-[var(--ink-muted)]">
            Future paid tiers (when enabled) will unlock higher monthly limits and advanced options. We will never charge
            from the frontend alone, and we will not invent “limited time” pressure.
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
