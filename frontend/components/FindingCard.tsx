const tone: Record<string, string> = {
  critical: "border-[var(--crimson)] bg-red-50",
  high: "border-amber-700 bg-amber-50",
  medium: "border-amber-600/60 bg-[var(--paper-2)]",
  low: "border-[var(--rule)] bg-[var(--paper-2)]",
  informational: "border-[var(--teal)]/40 bg-teal-50/40",
};

export function FindingCard({
  finding,
  onSelect,
}: {
  finding: {
    id: string;
    category: string;
    severity: string;
    location: string;
    explanation: string;
    suggestion: string;
  };
  onSelect?: () => void;
}) {
  return (
    <article className={`rounded-lg border-l-4 p-4 ${tone[finding.severity] || tone.medium}`}>
      <p className="text-xs font-semibold uppercase tracking-wide">
        <span className="sr-only">Severity: </span>
        {finding.severity} · {finding.category.replace("_", " ")}
      </p>
      <p className="mt-1 text-sm font-medium">{finding.location}</p>
      <p className="mt-2 text-sm leading-6">{finding.explanation}</p>
      {finding.suggestion && <p className="mt-2 text-sm text-[var(--teal)]">{finding.suggestion}</p>}
      {onSelect && (
        <button type="button" onClick={onSelect} className="mt-3 text-sm underline">
          Explain / teach me
        </button>
      )}
    </article>
  );
}
