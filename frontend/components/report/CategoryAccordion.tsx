"use client";

import Link from "next/link";
import { useId, useState } from "react";
import { categoryLabel, scoreTone } from "@/components/report/visuals";
import { ProgressBar } from "@/components/dashboard/primitives";
import { cn } from "@/lib/utils";

type Score = { category: string; score: number; rationale?: string };
type Finding = {
  id: string;
  category: string;
  severity: string;
  location: string;
  explanation: string;
  suggestion: string;
  teaching_note?: string;
  example?: string;
  original_text?: string;
  improved_sentence?: string;
};

const SECTION_ORDER = [
  "relevance",
  "thesis",
  "argument",
  "evidence",
  "structure",
  "academic_writing",
  "citations",
] as const;

const MERGE: Record<string, string> = {
  grammar: "academic_writing",
  references: "citations",
};

export function CategoryAccordion({
  scores,
  findings,
  strengths,
  weaknesses,
  assignmentId,
}: {
  scores: Score[];
  findings: Finding[];
  strengths: string[];
  weaknesses: string[];
  assignmentId: string;
}) {
  const baseId = useId();
  const [open, setOpen] = useState<string | null>(SECTION_ORDER[0]);

  const byCat: Record<string, Score> = {};
  for (const s of scores) {
    const key = MERGE[s.category] || s.category;
    if (!byCat[key] || s.score < byCat[key].score) {
      // prefer dedicated category; keep first seen average-ish by taking primary
      if (!byCat[key]) byCat[key] = { ...s, category: key };
      else if (s.category === key) byCat[key] = { ...s, category: key };
    }
  }

  const sections = SECTION_ORDER.filter((k) => byCat[k] || findings.some((f) => (MERGE[f.category] || f.category) === k));

  if (!sections.length) return null;

  return (
    <div className="space-y-3">
      {sections.map((key) => {
        const score = byCat[key];
        const catFindings = findings.filter((f) => (MERGE[f.category] || f.category) === key);
        const isOpen = open === key;
        const panelId = `${baseId}-${key}-panel`;
        const btnId = `${baseId}-${key}-btn`;
        const value = score?.score ?? 0;
        const status =
          value >= 75 ? "Strong" : value >= 55 ? "Developing" : value > 0 ? "Needs work" : "Not scored";
        const catStrengths = strengths.filter((s) => s.toLowerCase().includes(key.replaceAll("_", " ")) || s.toLowerCase().includes(categoryLabel(key).toLowerCase().split(" ")[0]));
        const catWeak = weaknesses.filter((s) => s.toLowerCase().includes(key.replaceAll("_", " ")) || s.toLowerCase().includes(categoryLabel(key).toLowerCase().split(" ")[0]));
        const coachQ = encodeURIComponent(`Help me improve ${categoryLabel(key).toLowerCase()} in this assignment.`);

        return (
          <div key={key} className="ac-surface overflow-hidden">
            <h3>
              <button
                type="button"
                id={btnId}
                aria-expanded={isOpen}
                aria-controls={panelId}
                className="flex w-full items-center gap-4 px-4 py-4 text-left transition-colors hover:bg-black/[0.02] md:px-5"
                onClick={() => setOpen(isOpen ? null : key)}
              >
                <span className="font-serif text-xl tabular-nums" style={{ color: scoreTone(value) }}>
                  {score ? value : "—"}
                </span>
                <span className="min-w-0 flex-1">
                  <span className="block font-medium text-[var(--ink)]">{categoryLabel(key)}</span>
                  <span className="mt-0.5 block text-xs text-[var(--ink-muted)]">
                    {status}
                    {catFindings.length ? ` · ${catFindings.length} finding${catFindings.length === 1 ? "" : "s"}` : ""}
                  </span>
                </span>
                <span className="text-sm text-[var(--teal)]" aria-hidden>
                  {isOpen ? "−" : "+"}
                </span>
              </button>
            </h3>
            <div
              id={panelId}
              role="region"
              aria-labelledby={btnId}
              hidden={!isOpen}
              className={cn(!isOpen && "hidden")}
            >
              <div className="border-t border-[var(--rule)] px-4 py-5 md:px-5">
                {score ? (
                  <div className="mb-4">
                    <ProgressBar value={score.score} />
                    {score.rationale ? (
                      <p className="mt-3 text-sm leading-7 text-[var(--ink-muted)]">{score.rationale}</p>
                    ) : null}
                  </div>
                ) : null}

                <div className="grid gap-4 md:grid-cols-2">
                  <div>
                    <p className="text-xs font-semibold uppercase tracking-wide text-[var(--forest)]">Strengths</p>
                    <ul className="mt-2 space-y-1.5 text-sm leading-6 text-[var(--ink)]">
                      {(catStrengths.length ? catStrengths : score && score.score >= 70 ? [score.rationale || "Holding up well in this dimension."] : ["No highlighted strength in this dimension yet."]).map(
                        (s, i) => (
                          <li key={`${key}-s-${i}`}>• {s}</li>
                        ),
                      )}
                    </ul>
                  </div>
                  <div>
                    <p className="text-xs font-semibold uppercase tracking-wide text-[var(--crimson)]">Weaknesses</p>
                    <ul className="mt-2 space-y-1.5 text-sm leading-6 text-[var(--ink)]">
                      {(catWeak.length
                        ? catWeak
                        : catFindings.length
                          ? catFindings.slice(0, 2).map((f) => f.explanation)
                          : ["No major weakness flagged."]
                      ).map((s, i) => (
                        <li key={`${key}-w-${i}`}>• {s}</li>
                      ))}
                    </ul>
                  </div>
                </div>

                {catFindings.length ? (
                  <div className="mt-5 space-y-3">
                    <p className="text-xs font-semibold uppercase tracking-wide text-[var(--ink-muted)]">
                      Recommendations & examples
                    </p>
                    {catFindings.slice(0, 3).map((f) => (
                      <article key={f.id} className="rounded-[var(--radius-sm)] border border-[var(--rule)] bg-[var(--paper)] px-3 py-3">
                        <p className="text-sm font-medium">{f.location || f.severity}</p>
                        {f.suggestion ? <p className="mt-1 text-sm leading-6 text-[var(--teal)]">{f.suggestion}</p> : null}
                        {f.example || f.improved_sentence ? (
                          <p className="mt-2 text-sm italic leading-6 text-[var(--ink-muted)]">
                            {f.example || f.improved_sentence}
                          </p>
                        ) : null}
                        {f.original_text && f.improved_sentence ? (
                          <div className="mt-3 grid gap-2 text-xs sm:grid-cols-2">
                            <div className="rounded border border-[var(--rule)] bg-[var(--paper-2)] p-2">
                              <p className="font-semibold text-[var(--ink-muted)]">Current</p>
                              <p className="mt-1 leading-5 text-[var(--ink)]">{f.original_text}</p>
                            </div>
                            <div className="rounded border border-[var(--teal)]/30 bg-[var(--teal-soft)]/50 p-2">
                              <p className="font-semibold text-[var(--teal)]">Improved</p>
                              <p className="mt-1 leading-5 text-[var(--ink)]">{f.improved_sentence}</p>
                            </div>
                          </div>
                        ) : null}
                      </article>
                    ))}
                  </div>
                ) : null}

                <div className="mt-5">
                  <Link
                    href={`/app/coach?assignment=${assignmentId}&q=${coachQ}`}
                    className="ac-hit inline-flex rounded-[var(--radius-sm)] border border-[var(--rule)] bg-[var(--paper-2)] px-4 text-sm font-medium text-[var(--teal)] hover:bg-[var(--teal-soft)]/50"
                  >
                    Ask Coach about {categoryLabel(key)}
                  </Link>
                </div>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
