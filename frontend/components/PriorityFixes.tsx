"use client";

import { Button } from "@/components/ui/Button";
import Link from "next/link";
import { cn } from "@/lib/utils";

export type PriorityFix = {
  id: string;
  title: string;
  why: string;
  impact: "Critical" | "High" | "Medium" | "Low";
  difficulty: "Easy" | "Moderate" | "Hard";
  expectedLift: string;
  liftPoints: number;
  timeToFix: string;
  category?: string;
};

const priorityTone: Record<PriorityFix["impact"], string> = {
  Critical: "bg-[var(--crimson)]/10 text-[var(--crimson)] border-[var(--crimson)]/25",
  High: "bg-amber-50 text-[var(--amber)] border-[var(--amber)]/30",
  Medium: "bg-[var(--paper)] text-[var(--ink-muted)] border-[var(--rule)]",
  Low: "bg-[var(--paper)] text-[var(--ink-muted)] border-[var(--rule)]",
};

export function PriorityFixes({
  items,
  onFix,
  coachHref,
}: {
  items: PriorityFix[];
  onFix?: (item: PriorityFix) => void;
  coachHref?: (item: PriorityFix) => string;
}) {
  if (!items.length) return null;
  return (
    <section aria-labelledby="fix-first-heading" className="ac-reveal ac-surface overflow-hidden">
      <div className="border-b border-[var(--rule)] bg-[var(--teal-soft)]/60 px-5 py-4 md:px-6">
        <h2 id="fix-first-heading" className="font-serif text-2xl text-[var(--ink)]">
          Top {Math.min(3, items.length)} Critical Fixes
        </h2>
        <p className="mt-1 text-sm text-[var(--ink-muted)]">
          What is wrong, what matters most, and what to fix first — with expected lift and time.
        </p>
      </div>
      <ol className="divide-y divide-[var(--rule)]">
        {items.map((item, index) => (
          <li
            key={item.id}
            className={cn(
              "grid gap-5 px-5 py-6 md:grid-cols-[auto_1fr_auto] md:items-start md:px-6",
              index === 0 && "bg-[var(--teal-soft)]/25",
            )}
          >
            <span className="font-serif text-3xl leading-none text-[var(--teal)]" aria-hidden>
              {String(index + 1).padStart(2, "0")}
            </span>
            <div className="min-w-0 space-y-4">
              <div>
                <p className="font-serif text-xl text-[var(--ink)] md:text-2xl">{item.title}</p>
                <p className="mt-2 max-w-2xl text-sm leading-7 text-[var(--ink-muted)]">{item.why}</p>
                {index === 0 ? (
                  <p className="mt-3 text-sm font-semibold text-[var(--teal)]">Fix this first.</p>
                ) : null}
              </div>
              <dl className="grid grid-cols-2 gap-3 sm:grid-cols-4">
                <div className="rounded-[var(--radius-sm)] border border-[var(--rule)] bg-[var(--paper-2)] px-3 py-2.5">
                  <dt className="text-[11px] uppercase tracking-wide text-[var(--ink-muted)]">Priority</dt>
                  <dd className="mt-1">
                    <span
                      className={cn(
                        "inline-flex rounded-full border px-2 py-0.5 text-xs font-semibold",
                        priorityTone[item.impact],
                      )}
                    >
                      {item.impact}
                    </span>
                  </dd>
                </div>
                <div className="rounded-[var(--radius-sm)] border border-[var(--rule)] bg-[var(--paper-2)] px-3 py-2.5">
                  <dt className="text-[11px] uppercase tracking-wide text-[var(--ink-muted)]">Est. improvement</dt>
                  <dd className="mt-1 font-serif text-xl tabular-nums text-[var(--forest)]">{item.expectedLift} points</dd>
                </div>
                <div className="rounded-[var(--radius-sm)] border border-[var(--rule)] bg-[var(--paper-2)] px-3 py-2.5">
                  <dt className="text-[11px] uppercase tracking-wide text-[var(--ink-muted)]">Difficulty</dt>
                  <dd className="mt-1 text-sm font-medium">{item.difficulty}</dd>
                </div>
                <div className="rounded-[var(--radius-sm)] border border-[var(--rule)] bg-[var(--paper-2)] px-3 py-2.5">
                  <dt className="text-[11px] uppercase tracking-wide text-[var(--ink-muted)]">Est. time</dt>
                  <dd className="mt-1 text-sm font-medium">{item.timeToFix}</dd>
                </div>
              </dl>
            </div>
            <div className="flex flex-wrap gap-2 justify-self-start md:flex-col md:justify-self-end">
              {onFix ? (
                <Button type="button" variant="primary" onClick={() => onFix(item)} className="w-full sm:w-auto">
                  Work on this
                </Button>
              ) : null}
              {coachHref ? (
                <Link
                  href={coachHref(item)}
                  className="ac-hit inline-flex w-full rounded-[var(--radius-sm)] border border-[var(--rule)] bg-[var(--paper-2)] px-4 text-sm font-medium text-[var(--teal)] sm:w-auto"
                >
                  Ask mentor
                </Link>
              ) : null}
            </div>
          </li>
        ))}
      </ol>
    </section>
  );
}

export function buildPriorityFixes(
  priorityActions: string[],
  scores: { category: string; score: number }[],
  findings: { category: string; severity: string; explanation?: string }[],
): PriorityFix[] {
  const scoreMap = Object.fromEntries(scores.map((s) => [s.category, s.score]));
  const actions =
    priorityActions.length > 0
      ? priorityActions.slice(0, 3)
      : scores
          .slice()
          .sort((a, b) => a.score - b.score)
          .slice(0, 3)
          .map((s) => `Improve ${s.category.replaceAll("_", " ")}`);

  return actions.map((title, i) => {
    const finding =
      findings.find((f) => title.toLowerCase().includes(f.category.replaceAll("_", " "))) || findings[i];
    const category = finding?.category || scores.slice().sort((a, b) => a.score - b.score)[i]?.category;
    const score = category ? scoreMap[category] : undefined;
    const severity =
      finding?.severity ||
      (score != null && score < 45 ? "critical" : score != null && score < 60 ? "high" : "medium");
    const impact: PriorityFix["impact"] =
      i === 0 && (severity === "critical" || severity === "high")
        ? "Critical"
        : severity === "critical" || severity === "high"
          ? "High"
          : severity === "medium"
            ? "Medium"
            : "Low";
    const difficulty: PriorityFix["difficulty"] =
      impact === "Critical" || impact === "High" ? (i === 0 ? "Easy" : "Moderate") : "Easy";
    const liftPoints =
      impact === "Critical" ? 8 + (i === 0 ? 2 : 0) : impact === "High" ? 6 : impact === "Medium" ? 4 : 3;
    const expectedLift = `+${liftPoints}`;
    const timeToFix =
      difficulty === "Easy" ? "10 minutes" : difficulty === "Moderate" ? "15 minutes" : "25 minutes";
    const why =
      finding?.explanation ||
      (score != null
        ? `This dimension sits at ${score}/100 — raising it moves the overall score fastest.`
        : "Addressing this first creates the clearest lift before your next check.");
    return {
      id: `fix-${i}`,
      title,
      why,
      impact,
      difficulty,
      expectedLift,
      liftPoints,
      timeToFix,
      category,
    };
  });
}
