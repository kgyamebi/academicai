import type { Metadata } from "next";
import { SiteFooter } from "@/components/SiteFooter";
import { SiteHeader } from "@/components/SiteHeader";

export const metadata: Metadata = {
  title: "Terms of use",
  description:
    "Terms for AcademicCheck AI: diagnostic study aid, not an official grade, not ghostwriting, and not a misconduct detector.",
  alternates: { canonical: "/terms" },
};

export default function TermsPage() {
  return (
    <>
      <SiteHeader />
      <main id="main-content" tabIndex={-1} className="mx-auto max-w-3xl px-4 py-16 md:py-20">
        <p className="text-sm font-medium tracking-wide text-[var(--teal)]">Legal</p>
        <h1 className="mt-3 font-serif text-4xl md:text-5xl">Terms of use</h1>
        <p className="mt-4 text-sm text-[var(--ink-muted)]">Last updated: September 2026 · Public free launch</p>

        <div className="mt-10 space-y-8 text-sm leading-7 text-[var(--ink)]">
          <section>
            <h2 className="font-serif text-2xl">What AcademicCheck AI is</h2>
            <p className="mt-3 text-[var(--ink-muted)]">
              AcademicCheck AI provides diagnostic feedback on academic writing: how well a draft addresses an assignment
              question, structure, argument, evidence, and citations. It is a study aid — not an official grade, not a
              misconduct detector, and not a substitute for your lecturer or institution policies.
            </p>
          </section>

          <section>
            <h2 className="font-serif text-2xl">What we do not claim</h2>
            <ul className="mt-3 list-disc space-y-2 pl-5 text-[var(--ink-muted)]">
              <li>We do not guarantee marks, acceptance, or publication outcomes.</li>
              <li>We do not write complete assignments for submission on your behalf.</li>
              <li>We do not invent sources, fabricate quotations, or invent statistics.</li>
              <li>We do not sell your documents or use them for model training by default.</li>
            </ul>
          </section>

          <section>
            <h2 className="font-serif text-2xl">Your responsibilities</h2>
            <p className="mt-3 text-[var(--ink-muted)]">
              You are responsible for the content you upload, for following your institution’s academic integrity rules,
              and for deciding what feedback to apply. Do not upload material you are not allowed to share.
            </p>
          </section>

          <section>
            <h2 className="font-serif text-2xl">Accounts and free launch</h2>
            <p className="mt-3 text-[var(--ink-muted)]">
              During the public free launch, paid subscriptions and checkout are disabled. Fair-use limits may apply so
              the service stays reliable. We may change limits or availability with reasonable notice when paid plans
              return.
            </p>
          </section>

          <section>
            <h2 className="font-serif text-2xl">Privacy and deletion</h2>
            <p className="mt-3 text-[var(--ink-muted)]">
              Guest uploads are retained briefly. Account documents remain until you delete them or a retention policy
              applies. See{" "}
              <a href="/help/privacy" className="text-[var(--teal)] underline-offset-4 hover:underline">
                Privacy and data deletion
              </a>{" "}
              for details. Account deletion disables login and removes document text; records required by law may be
              retained.
            </p>
          </section>

          <section>
            <h2 className="font-serif text-2xl">Contact</h2>
            <p className="mt-3 text-[var(--ink-muted)]">
              Questions about these terms:{" "}
              <a href="/contact" className="text-[var(--teal)] underline-offset-4 hover:underline">
                Contact us
              </a>
              .
            </p>
          </section>
        </div>
      </main>
      <SiteFooter />
    </>
  );
}
