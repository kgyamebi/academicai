import { SiteFooter } from "@/components/SiteFooter";
import { SiteHeader } from "@/components/SiteHeader";

export default function SecurityPage() {
  return (
    <>
      <SiteHeader />
      <main id="main-content" tabIndex={-1} className="mx-auto max-w-3xl px-4 py-16 md:py-20">
        <p className="text-sm font-medium tracking-wide text-[var(--teal)]">Security</p>
        <h1 className="mt-3 font-serif text-4xl md:text-5xl">How we protect coursework.</h1>
        <p className="mt-5 text-lg leading-8 text-[var(--ink-muted)]">
          Plain-language security for students and institutions. This is not a penetration-test certificate.
        </p>
        <ul className="mt-10 space-y-6 text-sm leading-7 text-[var(--ink)]">
          <li>
            <p className="font-medium">Tenant isolation</p>
            <p className="text-[var(--ink-muted)]">
              Assignments, documents, reports, and shares are scoped to the signed-in account on the server — not only in the UI.
            </p>
          </li>
          <li>
            <p className="font-medium">Encrypted fields</p>
            <p className="text-[var(--ink-muted)]">
              Sensitive draft content is field-encrypted at rest when encryption keys are configured. Losing those keys loses readability — we treat them as critical secrets.
            </p>
          </li>
          <li>
            <p className="font-medium">Uploads</p>
            <p className="text-[var(--ink-muted)]">
              Files are validated by signature and size limits. Executable disguises are rejected. Optional malware scanning can be enabled in production.
            </p>
          </li>
          <li>
            <p className="font-medium">Sessions & CSRF</p>
            <p className="text-[var(--ink-muted)]">
              Cookie sessions with CSRF protection on state-changing requests. Production should run with secure cookies over HTTPS.
            </p>
          </li>
          <li>
            <p className="font-medium">What we do not claim</p>
            <p className="text-[var(--ink-muted)]">
              We do not claim guaranteed grades, human grading, or perfect detection accuracy. AI feedback is diagnostic only.
            </p>
          </li>
        </ul>
        <p className="mt-10 text-sm text-[var(--ink-muted)]">
          Questions:{" "}
          <a className="text-[var(--teal)] underline-offset-4 hover:underline" href="mailto:hello@academiccheck.ai">
            hello@academiccheck.ai
          </a>
        </p>
      </main>
      <SiteFooter />
    </>
  );
}
