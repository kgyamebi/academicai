export function ScoreRing({ score, label }: { score: number; label?: string }) {
  const clamped = Math.max(0, Math.min(100, score));
  return (
    <div className="flex items-center gap-4">
      <div
        className="grid h-24 w-24 place-items-center rounded-full border-8 border-[var(--teal)] bg-[var(--paper-2)]"
        role="img"
        aria-label={`Diagnostic score ${clamped} out of 100`}
      >
        <span className="font-serif text-2xl">{clamped}</span>
      </div>
      <div>
        <p className="text-sm uppercase tracking-wide text-[var(--ink-muted)]">{label || "Overall writing quality"}</p>
        <p className="max-w-xs text-sm text-[var(--ink-muted)]">AI-assisted diagnostic indicator — not an official grade.</p>
      </div>
    </div>
  );
}
