"use client";

export function ScoreRing({
  score,
  label,
  size = "lg",
}: {
  score: number;
  label?: string;
  size?: "sm" | "md" | "lg";
}) {
  const clamped = Math.max(0, Math.min(100, Math.round(score)));
  const dims = { sm: 72, md: 96, lg: 128 }[size];
  const stroke = size === "sm" ? 6 : size === "md" ? 8 : 10;
  const r = (dims - stroke) / 2;
  const c = 2 * Math.PI * r;
  const offset = c - (clamped / 100) * c;
  const tone =
    clamped >= 75 ? "var(--forest)" : clamped >= 55 ? "var(--teal)" : clamped >= 40 ? "var(--amber)" : "var(--crimson)";

  return (
    <div className="flex items-center gap-5">
      <div className="relative" style={{ width: dims, height: dims }} role="img" aria-label={`Diagnostic score ${clamped} out of 100`}>
        <svg width={dims} height={dims} className="-rotate-90" aria-hidden>
          <circle cx={dims / 2} cy={dims / 2} r={r} fill="none" stroke="var(--rule)" strokeWidth={stroke} />
          <circle
            cx={dims / 2}
            cy={dims / 2}
            r={r}
            fill="none"
            stroke={tone}
            strokeWidth={stroke}
            strokeLinecap="round"
            strokeDasharray={c}
            strokeDashoffset={offset}
            className="transition-[stroke-dashoffset] duration-700 ease-out"
          />
        </svg>
        <div className="absolute inset-0 grid place-items-center">
          <span className="font-serif text-3xl tabular-nums text-[var(--ink)]" style={{ fontSize: size === "lg" ? undefined : size === "md" ? "1.5rem" : "1.15rem" }}>
            {clamped}
          </span>
        </div>
      </div>
      <div className="min-w-0">
        <p className="text-sm font-medium uppercase tracking-wide text-[var(--ink-muted)]">
          {label || "Academic health"}
        </p>
        <p className="mt-1 max-w-xs text-sm leading-6 text-[var(--ink-muted)]">
          AI-assisted diagnostic indicator — not an official grade.
        </p>
      </div>
    </div>
  );
}
