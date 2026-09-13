"use client";

const LABELS: Record<string, string> = {
  relevance: "Question fit",
  thesis: "Thesis",
  argument: "Argument",
  evidence: "Evidence",
  structure: "Structure",
  writing: "Writing",
  academic_writing: "Writing",
  citations: "Citations",
  grammar: "Writing",
};

export function DimensionStrip({
  scores,
}: {
  scores: { category: string; score: number; rationale?: string }[];
}) {
  if (!scores.length) return null;
  return (
    <section aria-label="Performance dimensions" className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
      {scores.map((s) => {
        const label = LABELS[s.category] || s.category.replaceAll("_", " ");
        const tone =
          s.score >= 75 ? "var(--forest)" : s.score >= 55 ? "var(--teal)" : s.score >= 40 ? "var(--amber)" : "var(--crimson)";
        return (
          <article key={s.category} className="ac-surface p-4">
            <div className="flex items-baseline justify-between gap-3">
              <h3 className="text-sm font-medium capitalize text-[var(--ink)]">{label}</h3>
              <p className="font-serif text-2xl tabular-nums" style={{ color: tone }}>
                {s.score}
              </p>
            </div>
            <div className="mt-3 h-1.5 overflow-hidden rounded-full bg-[var(--rule)]" aria-hidden>
              <div className="h-full rounded-full transition-all duration-500" style={{ width: `${s.score}%`, background: tone }} />
            </div>
            {s.rationale ? (
              <p className="mt-3 text-sm leading-6 text-[var(--ink-muted)] line-clamp-3">{s.rationale}</p>
            ) : null}
          </article>
        );
      })}
    </section>
  );
}
