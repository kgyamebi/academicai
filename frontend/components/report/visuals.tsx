"use client";

import { cn } from "@/lib/utils";

const LABELS: Record<string, string> = {
  relevance: "Question Relevance",
  thesis: "Thesis Strength",
  argument: "Argument Quality",
  evidence: "Evidence Quality",
  structure: "Structure",
  academic_writing: "Writing Style",
  grammar: "Writing Style",
  citations: "Citation Accuracy",
  references: "Citation Accuracy",
};

export function categoryLabel(category: string) {
  return LABELS[category] || category.replaceAll("_", " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

export function scoreTone(score: number) {
  if (score >= 75) return "var(--forest)";
  if (score >= 55) return "var(--teal)";
  if (score >= 40) return "var(--amber)";
  return "var(--crimson)";
}

/** Pure SVG radar — no chart library dependency. */
export function RadarChart({
  scores,
  className,
}: {
  scores: { category: string; score: number }[];
  className?: string;
}) {
  const items = scores.slice(0, 8);
  if (items.length < 3) return null;
  const size = 220;
  const cx = size / 2;
  const cy = size / 2;
  const radius = 78;
  const n = items.length;

  function point(i: number, value: number) {
    const angle = -Math.PI / 2 + (i / n) * Math.PI * 2;
    const r = (Math.max(0, Math.min(100, value)) / 100) * radius;
    return [cx + Math.cos(angle) * r, cy + Math.sin(angle) * r] as const;
  }

  const poly = items.map((s, i) => point(i, s.score).join(",")).join(" ");
  const rings = [25, 50, 75, 100];

  return (
    <div className={cn("mx-auto w-full max-w-[280px]", className)}>
      <svg viewBox={`0 0 ${size} ${size}`} role="img" aria-label="Category radar chart of diagnostic scores" className="w-full">
        {rings.map((ring) => (
          <polygon
            key={ring}
            fill="none"
            stroke="var(--rule)"
            strokeWidth="1"
            points={items.map((_, i) => point(i, ring).join(",")).join(" ")}
          />
        ))}
        {items.map((_, i) => {
          const [x, y] = point(i, 100);
          return <line key={`axis-${i}`} x1={cx} y1={cy} x2={x} y2={y} stroke="var(--rule)" strokeWidth="1" />;
        })}
        <polygon points={poly} fill="rgba(15, 118, 110, 0.18)" stroke="var(--teal)" strokeWidth="2" />
        {items.map((s, i) => {
          const [x, y] = point(i, s.score);
          return <circle key={s.category} cx={x} cy={y} r="3.5" fill="var(--teal)" />;
        })}
      </svg>
      <ul className="mt-2 flex flex-wrap justify-center gap-x-3 gap-y-1 text-[11px] text-[var(--ink-muted)]">
        {items.map((s) => (
          <li key={s.category}>
            {categoryLabel(s.category)} · {s.score}
          </li>
        ))}
      </ul>
    </div>
  );
}

export function ScoreHeatmap({ scores }: { scores: { category: string; score: number }[] }) {
  if (!scores.length) return null;
  return (
    <div role="group" aria-label="Score heatmap" className="grid grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-4">
      {scores.map((s) => {
        const tone = scoreTone(s.score);
        const intensity = Math.max(0.12, s.score / 100);
        return (
          <div
            key={s.category}
            className="rounded-[var(--radius-sm)] border border-[var(--rule)] px-3 py-3"
            style={{ background: `color-mix(in srgb, ${tone} ${Math.round(intensity * 35)}%, white)` }}
          >
            <p className="text-[11px] font-medium uppercase tracking-wide text-[var(--ink-muted)]">
              {categoryLabel(s.category)}
            </p>
            <p className="mt-1 font-serif text-2xl tabular-nums" style={{ color: tone }}>
              {s.score}
            </p>
          </div>
        );
      })}
    </div>
  );
}

export function SeverityBucket({
  title,
  items,
  tone,
  onSelect,
  empty,
}: {
  title: string;
  items: { id: string; location: string; category: string; explanation: string }[];
  tone: "critical" | "important" | "minor";
  onSelect?: (id: string) => void;
  empty: string;
}) {
  const border =
    tone === "critical"
      ? "border-[var(--crimson)]/40"
      : tone === "important"
        ? "border-[var(--amber)]/40"
        : "border-[var(--rule)]";
  const badge =
    tone === "critical"
      ? "bg-red-50 text-[var(--crimson)]"
      : tone === "important"
        ? "bg-amber-50 text-[var(--amber)]"
        : "bg-[var(--paper)] text-[var(--ink-muted)]";

  return (
    <section className={cn("ac-surface overflow-hidden border", border)}>
      <div className="flex items-center justify-between gap-2 border-b border-[var(--rule)] px-4 py-3">
        <h3 className="font-serif text-lg">{title}</h3>
        <span className={cn("rounded-full px-2.5 py-0.5 text-xs font-semibold", badge)}>{items.length}</span>
      </div>
      {items.length === 0 ? (
        <p className="px-4 py-4 text-sm text-[var(--ink-muted)]">{empty}</p>
      ) : (
        <ul className="divide-y divide-[var(--rule)]">
          {items.map((item) => (
            <li key={item.id} className="px-4 py-3">
              <p className="text-sm font-medium">{item.location || categoryLabel(item.category)}</p>
              <p className="mt-1 text-sm leading-6 text-[var(--ink-muted)] line-clamp-2">{item.explanation}</p>
              {onSelect ? (
                <button
                  type="button"
                  className="ac-hit mt-2 justify-start text-sm font-medium text-[var(--teal)] underline-offset-4 hover:underline"
                  onClick={() => onSelect(item.id)}
                >
                  Focus this finding
                </button>
              ) : null}
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
