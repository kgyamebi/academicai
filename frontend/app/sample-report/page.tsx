import Link from "next/link";
import { SiteFooter } from "@/components/SiteFooter";
import { SiteHeader } from "@/components/SiteHeader";
import { ButtonLink } from "@/components/ui/Button";

/**
 * Illustrative sample only — not a live analysis, not a real student paper.
 * Conversion asset for visitors before signup.
 */
const SAMPLE = {
  score: 72,
  readiness: "Almost Ready",
  potential: 14,
  minutes: 35,
  summary:
    "The draft addresses the question but the thesis is still descriptive. Evidence is present; several claims need closer source integration. Citations are mostly consistent with APA 7 with a few formatting gaps.",
  fixes: [
    {
      title: "Sharpen the thesis into a contestable claim",
      priority: "Critical",
      lift: "+8",
      difficulty: "Easy",
      time: "10 minutes",
      why: "The opening states a topic rather than an arguable position that answers the command word.",
    },
    {
      title: "Deepen evidence in paragraphs 3–4",
      priority: "High",
      lift: "+6",
      difficulty: "Moderate",
      time: "15 minutes",
      why: "Claims move faster than the sources support. Add one stronger citation or quotation per key claim.",
    },
    {
      title: "Citation consistency (APA 7)",
      priority: "High",
      lift: "+4",
      difficulty: "Easy",
      time: "10 minutes",
      why: "Reference list and in-text years are mostly aligned; a handful of entries need italics and DOI formatting.",
    },
  ],
  strengths: [
    "Clear awareness of the assignment question",
    "Readable structure with topic sentences",
    "Honest engagement with opposing views",
  ],
  weaknesses: [
    "Thesis still descriptive",
    "Uneven source integration",
    "Conclusion restates rather than synthesizes",
  ],
  opportunity: {
    area: "Thesis & question fit",
    body: "Turning the thesis into a contestable claim unlocks clearer paragraph purpose and a stronger conclusion.",
  },
};

export default function SampleReportPage() {
  return (
    <>
      <SiteHeader />
      <main id="main-content" tabIndex={-1} className="mx-auto max-w-3xl px-4 py-12 md:py-16">
        <p className="text-sm font-medium tracking-wide text-[var(--teal)]">Illustrative sample</p>
        <h1 className="mt-2 font-serif text-4xl md:text-5xl">Academic Performance Overview</h1>
        <p className="mt-4 max-w-2xl text-sm leading-7 text-[var(--ink-muted)]">
          This is a <strong className="font-medium text-[var(--ink)]">sample report layout</strong> — not a live
          analysis of a real paper, and not a promise of any score. Use it to see how AcademicCheck AI presents
          priorities, readiness, and next steps.
        </p>

        <section className="ac-reveal mt-10 overflow-hidden rounded-[var(--radius-lg)] border border-[var(--rule)] bg-[var(--paper-2)]">
          <div className="grid gap-6 p-6 md:grid-cols-[auto_1fr] md:items-center md:p-8">
            <div className="flex h-28 w-28 items-center justify-center rounded-full border-[6px] border-[var(--teal)]/35">
              <span className="font-serif text-4xl tabular-nums">{SAMPLE.score}</span>
            </div>
            <div>
              <p className="font-serif text-2xl md:text-3xl">
                {SAMPLE.score} <span className="text-lg text-[var(--ink-muted)]">Overall Score</span>
              </p>
              <p className="mt-2 text-lg font-medium text-[var(--teal)]">{SAMPLE.readiness}</p>
              <p className="mt-3 text-sm leading-7 text-[var(--ink)]">{SAMPLE.summary}</p>
              <dl className="mt-5 grid gap-3 sm:grid-cols-2">
                <div className="rounded-[var(--radius-sm)] border border-[var(--rule)] px-3 py-3">
                  <dt className="text-xs uppercase tracking-wide text-[var(--ink-muted)]">Improvement potential</dt>
                  <dd className="mt-1 font-serif text-xl text-[var(--forest)]">+{SAMPLE.potential}</dd>
                </div>
                <div className="rounded-[var(--radius-sm)] border border-[var(--rule)] px-3 py-3">
                  <dt className="text-xs uppercase tracking-wide text-[var(--ink-muted)]">Time to improve</dt>
                  <dd className="mt-1 font-medium">~{SAMPLE.minutes} minutes</dd>
                </div>
              </dl>
            </div>
          </div>
        </section>

        <section className="ac-surface mt-8 overflow-hidden" aria-labelledby="sample-fixes">
          <div className="border-b border-[var(--rule)] bg-[var(--teal-soft)]/60 px-5 py-4">
            <h2 id="sample-fixes" className="font-serif text-2xl">
              Top 3 Critical Fixes
            </h2>
            <p className="mt-1 text-sm text-[var(--ink-muted)]">What matters most — fix these first.</p>
          </div>
          <ol className="divide-y divide-[var(--rule)]">
            {SAMPLE.fixes.map((f, i) => (
              <li key={f.title} className="grid gap-4 px-5 py-5 md:grid-cols-[auto_1fr]">
                <span className="font-serif text-2xl text-[var(--teal)]" aria-hidden>
                  {String(i + 1).padStart(2, "0")}
                </span>
                <div>
                  <p className="font-serif text-xl">{f.title}</p>
                  <p className="mt-2 text-sm leading-7 text-[var(--ink-muted)]">{f.why}</p>
                  {i === 0 ? <p className="mt-2 text-sm font-semibold text-[var(--teal)]">Fix this first.</p> : null}
                  <dl className="mt-4 grid grid-cols-2 gap-2 sm:grid-cols-4 text-xs">
                    <div>
                      <dt className="text-[var(--ink-muted)]">Priority</dt>
                      <dd className="mt-0.5 font-semibold text-[var(--crimson)]">{f.priority}</dd>
                    </div>
                    <div>
                      <dt className="text-[var(--ink-muted)]">Est. improvement</dt>
                      <dd className="mt-0.5 font-semibold text-[var(--forest)]">{f.lift} points</dd>
                    </div>
                    <div>
                      <dt className="text-[var(--ink-muted)]">Difficulty</dt>
                      <dd className="mt-0.5 font-medium">{f.difficulty}</dd>
                    </div>
                    <div>
                      <dt className="text-[var(--ink-muted)]">Est. time</dt>
                      <dd className="mt-0.5 font-medium">{f.time}</dd>
                    </div>
                  </dl>
                </div>
              </li>
            ))}
          </ol>
        </section>

        <section className="ac-surface mt-8 p-5 md:p-6" aria-labelledby="sample-opp">
          <h2 id="sample-opp" className="font-serif text-2xl">
            Biggest Improvement Opportunity
          </h2>
          <p className="mt-2 text-sm font-medium text-[var(--teal)]">{SAMPLE.opportunity.area}</p>
          <p className="mt-2 text-sm leading-7 text-[var(--ink-muted)]">{SAMPLE.opportunity.body}</p>
        </section>

        <div className="mt-8 grid gap-6 md:grid-cols-2">
          <section className="ac-surface p-5">
            <h2 className="font-serif text-xl">Key Strengths</h2>
            <ul className="mt-3 list-disc space-y-2 pl-5 text-sm leading-6">
              {SAMPLE.strengths.map((s) => (
                <li key={s}>{s}</li>
              ))}
            </ul>
          </section>
          <section className="ac-surface p-5">
            <h2 className="font-serif text-xl">Key Weaknesses</h2>
            <ul className="mt-3 list-disc space-y-2 pl-5 text-sm leading-6">
              {SAMPLE.weaknesses.map((s) => (
                <li key={s}>{s}</li>
              ))}
            </ul>
          </section>
        </div>

        <section className="mt-10 rounded-[var(--radius-lg)] border border-[var(--teal)]/30 bg-[var(--teal-soft)]/40 p-6 md:p-8">
          <h2 className="font-serif text-2xl">See this on your own draft</h2>
          <p className="mt-2 text-sm leading-7 text-[var(--ink-muted)]">
            No account required for a first look. Create a free account later to save reports and track Academic
            Progress.
          </p>
          <div className="mt-6 flex flex-wrap gap-3">
            <ButtonLink href="/check" variant="primary">
              Analyze your essay
            </ButtonLink>
            <ButtonLink href="/register" variant="secondary">
              Create free account
            </ButtonLink>
          </div>
          <p className="mt-4 text-xs leading-6 text-[var(--ink-muted)]">
            Diagnostic feedback only — not an official grade.{" "}
            <Link href="/help/academic-integrity" className="underline-offset-4 hover:underline">
              Academic integrity
            </Link>
          </p>
        </section>
      </main>
      <SiteFooter />
    </>
  );
}
