import Link from "next/link";
import { SiteFooter } from "@/components/SiteFooter";
import { SiteHeader } from "@/components/SiteHeader";
import { messages } from "@/lib/i18n";

const modules = [
  "Assignment question analysis",
  "Thesis checking",
  "Argument analysis",
  "Citation checking",
  "Rubric alignment",
  "Academic writing feedback",
  "Version comparison",
];

export default function HomePage() {
  return (
    <>
      <SiteHeader />
      <main>
        <section className="mx-auto max-w-6xl px-4 py-16 md:py-24">
          <p className="text-sm uppercase tracking-[0.2em] text-[var(--teal)]">Academic writing analysis</p>
          <h1 className="mt-4 max-w-3xl font-serif text-4xl leading-tight md:text-6xl">{messages.heroTitle}</h1>
          <p className="mt-6 max-w-2xl text-lg leading-8 text-[var(--ink-muted)]">{messages.heroSub}</p>
          <div className="mt-8 flex flex-col gap-3 sm:flex-row">
            <Link href="/check" className="rounded-md bg-[var(--teal)] px-5 py-3 text-center text-white">
              {messages.primaryCta}
            </Link>
            <Link href="#how-it-works" className="rounded-md border border-[var(--rule)] px-5 py-3 text-center">
              {messages.secondaryCta}
            </Link>
          </div>
          <p className="mt-6 max-w-2xl text-sm leading-6 text-[var(--ink-muted)]">{messages.disclaimer}</p>
        </section>

        <section className="border-y border-[var(--rule)] bg-[var(--paper-2)]">
          <div className="mx-auto grid max-w-6xl gap-4 px-4 py-10 md:grid-cols-3">
            {modules.map((item) => (
              <p key={item} className="rounded-lg border border-[var(--rule)] px-4 py-3 text-sm">
                {item}
              </p>
            ))}
          </div>
        </section>

        <section id="how-it-works" className="mx-auto max-w-6xl px-4 py-16">
          <h2 className="font-serif text-3xl">How it works</h2>
          <ol className="mt-8 grid gap-4 md:grid-cols-4">
            {[
              ["1", "Add the question", "Paste the assignment prompt so the checker can interpret command words and scope."],
              ["2", "Upload your draft", "Paste text or upload DOCX/PDF. Files are validated by signature, not extension alone."],
              ["3", "Read the diagnosis", "See relevance, thesis, argument, evidence, structure, writing and citations."],
              ["4", "Fix the weakest area", "Work on the highest-impact issue, then re-check and compare drafts."],
            ].map(([n, title, body]) => (
              <li key={n} className="rounded-xl border border-[var(--rule)] bg-[var(--paper-2)] p-5">
                <p className="font-serif text-2xl text-[var(--teal)]">{n}</p>
                <h3 className="mt-2 font-serif text-xl">{title}</h3>
                <p className="mt-2 text-sm leading-6 text-[var(--ink-muted)]">{body}</p>
              </li>
            ))}
          </ol>
        </section>
      </main>
      <SiteFooter />
    </>
  );
}
