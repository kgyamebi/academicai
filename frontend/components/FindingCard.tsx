import { AlertOctagon, AlertTriangle, Info, MinusCircle } from "lucide-react";

const tone: Record<string, string> = {
  critical: "border-[var(--crimson)] bg-red-50",
  high: "border-amber-700 bg-amber-50",
  medium: "border-amber-600/60 bg-[var(--paper-2)]",
  low: "border-[var(--rule)] bg-[var(--paper-2)]",
  informational: "border-[var(--teal)]/40 bg-teal-50/40",
};

const severityMeta: Record<string, { icon: typeof AlertOctagon; label: string }> = {
  critical: { icon: AlertOctagon, label: "Critical warning" },
  high: { icon: AlertTriangle, label: "High warning" },
  medium: { icon: AlertTriangle, label: "Medium warning" },
  low: { icon: MinusCircle, label: "Low notice" },
  informational: { icon: Info, label: "Informational notice" },
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
  const meta = severityMeta[finding.severity] || severityMeta.medium;
  const Icon = meta.icon;
  return (
    <article className={`rounded-[var(--radius-md)] border border-l-4 p-4 ${tone[finding.severity] || tone.medium}`}>
      <p className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wide">
        <Icon aria-hidden="true" className="h-3.5 w-3.5 shrink-0" />
        <span className="sr-only">{meta.label}. </span>
        {finding.severity} · {finding.category.replaceAll("_", " ")}
      </p>
      <p className="mt-2 text-sm font-medium text-[var(--ink)]">{finding.location}</p>
      <p className="mt-2 text-sm leading-6 text-[var(--ink)]">{finding.explanation}</p>
      {finding.suggestion ? <p className="mt-2 text-sm leading-6 text-[var(--teal)]">{finding.suggestion}</p> : null}
      {onSelect ? (
        <button type="button" onClick={onSelect} className="ac-hit mt-3 justify-start text-sm font-medium text-[var(--teal)] underline-offset-4 hover:underline">
          Explain / teach me
        </button>
      ) : null}
    </article>
  );
}
