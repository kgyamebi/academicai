import { SiteFooter } from "@/components/SiteFooter";
import { SiteHeader } from "@/components/SiteHeader";

export default function ContactPage() {
  return (
    <>
      <SiteHeader />
      <main id="main-content" tabIndex={-1} className="mx-auto max-w-3xl px-4 py-16 md:py-20">
        <p className="text-sm font-medium tracking-wide text-[var(--teal)]">Contact</p>
        <h1 className="mt-3 font-serif text-4xl md:text-5xl">Talk to a human.</h1>
        <p className="mt-5 max-w-xl text-lg leading-8 text-[var(--ink-muted)]">
          Questions about privacy, integrity, plans, or access — write to us. We respond as people, not as a bot funnel.
        </p>
        <div className="ac-surface mt-10 p-6">
          <p className="text-sm font-medium text-[var(--ink-muted)]">Email</p>
          <p className="mt-2 font-serif text-2xl">
            <a className="text-[var(--teal)] underline-offset-4 hover:underline" href="mailto:hello@academiccheck.ai">
              hello@academiccheck.ai
            </a>
          </p>
          <p className="mt-4 text-sm leading-7 text-[var(--ink-muted)]">
            For data deletion requests, use Settings after signing in, or email with the subject line “Data deletion”.
          </p>
        </div>
        <ul className="mt-8 space-y-2 text-sm text-[var(--ink-muted)]">
          <li>
            <a className="text-[var(--teal)] underline-offset-4 hover:underline" href="/help/privacy">
              Privacy
            </a>
          </li>
          <li>
            <a className="text-[var(--teal)] underline-offset-4 hover:underline" href="/help/academic-integrity">
              Academic integrity
            </a>
          </li>
          <li>
            <a className="text-[var(--teal)] underline-offset-4 hover:underline" href="/about">
              About
            </a>
          </li>
        </ul>
      </main>
      <SiteFooter />
    </>
  );
}
