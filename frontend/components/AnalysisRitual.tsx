"use client";

export type UploadPhase =
  | "idle"
  | "dragging"
  | "uploading"
  | "processing"
  | "analyzing"
  | "generating"
  | "completed"
  | "failed";

type DisplayStep = {
  id: string;
  label: string;
  match: RegExp;
};

/** User-facing ritual steps — more granular than API phases. */
const DISPLAY_STEPS: DisplayStep[] = [
  { id: "uploading", label: "Uploading", match: /upload/i },
  { id: "processing", label: "Processing", match: /extract|document|queued|process/i },
  { id: "structure", label: "Analyzing Structure", match: /structure|question|thesis|interpret/i },
  { id: "arguments", label: "Analyzing Arguments", match: /argument|evidence|writ|grammar|analy/i },
  { id: "citations", label: "Checking Citations", match: /citation|reference/i },
  { id: "generating", label: "Generating Report", match: /complet|report|scor|build|generat/i },
];

const PHASE_COPY: Record<UploadPhase, { title: string; body: string }> = {
  idle: { title: "Ready when you are", body: "Paste a draft or upload a file to begin." },
  dragging: { title: "Drop to upload", body: "Release to attach your PDF, DOCX, TXT, or MD file." },
  uploading: { title: "Uploading", body: "Sending your draft securely…" },
  processing: { title: "Processing", body: "Extracting text and validating the document…" },
  analyzing: { title: "Analyzing", body: "Reviewing structure, arguments, and citations…" },
  generating: { title: "Generating report", body: "Assembling your Academic Performance Overview…" },
  completed: { title: "Report ready", body: "Your Academic Performance Overview is ready." },
  failed: {
    title: "Analysis could not finish",
    body: "Something went wrong. Use Try again, or open your dashboard — you will not be left on a spinning screen.",
  },
};

function resolvePhase(phase: UploadPhase | undefined, stage?: string, status?: string): UploadPhase {
  if (phase) return phase;
  const raw = `${stage || ""} ${status || ""}`;
  if (/fail|error|cancel/i.test(raw)) return "failed";
  if (/complet|succeeded|success/i.test(status || "") || /complet/i.test(stage || "")) return "completed";
  if (/upload/i.test(raw)) return "uploading";
  if (/extract|document|queued|process/i.test(raw)) return "processing";
  if (/report|scor|build|generat/i.test(raw)) return "generating";
  return "analyzing";
}

function activeDisplayIndex(phase: UploadPhase, stage?: string, status?: string): number {
  if (phase === "completed") return DISPLAY_STEPS.length - 1;
  if (phase === "uploading") return 0;
  if (phase === "processing") return 1;
  if (phase === "generating") return DISPLAY_STEPS.length - 1;
  const raw = `${stage || ""} ${status || ""} ${phase}`;
  const idx = DISPLAY_STEPS.findIndex((s) => s.match.test(raw));
  if (idx >= 0) return idx;
  if (phase === "analyzing") return 2;
  return 0;
}

export function AnalysisRitual({
  stage,
  status,
  phase,
  onRetry,
}: {
  stage?: string;
  status?: string;
  phase?: UploadPhase;
  onRetry?: () => void;
}) {
  const current = resolvePhase(phase, stage, status);
  const failed = current === "failed";
  const completed = current === "completed";
  const copy = PHASE_COPY[current];
  const activeIndex = activeDisplayIndex(current, stage, status);
  const progressPct = completed
    ? 100
    : failed
      ? Math.round(((activeIndex + 1) / DISPLAY_STEPS.length) * 100)
      : Math.round(((activeIndex + 0.4) / DISPLAY_STEPS.length) * 100);

  const steps = DISPLAY_STEPS.map((step, i) => ({
    ...step,
    state: failed
      ? i <= activeIndex
        ? "done"
        : "pending"
      : i < activeIndex
        ? "done"
        : i === activeIndex
          ? "active"
          : "pending",
  }));

  return (
    <div className="ac-reveal ac-surface p-5 md:p-6" aria-live="polite" aria-busy={!completed && !failed}>
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-sm font-semibold text-[var(--teal)]">{copy.title}</p>
          <p className="mt-1 text-sm leading-6 text-[var(--ink-muted)]">
            {completed || failed ? copy.body : `${copy.body}`}
          </p>
        </div>
        {!completed && !failed ? (
          <p className="text-xs font-medium tabular-nums text-[var(--ink-muted)]" aria-hidden>
            {progressPct}%
          </p>
        ) : null}
      </div>

      <div
        className="mt-4 h-1.5 overflow-hidden rounded-full bg-[var(--rule)]"
        role="progressbar"
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={progressPct}
        aria-label="Analysis progress"
      >
        <div
          className={`h-full rounded-full transition-[width] duration-500 ease-out ${failed ? "bg-[var(--crimson)]" : "bg-[var(--teal)]"}`}
          style={{ width: `${progressPct}%` }}
        />
      </div>

      <ol className="mt-5 space-y-3">
        {steps.map((step) => (
          <li key={step.id} className="flex items-center gap-3 text-sm">
            <span
              className={`h-2.5 w-2.5 shrink-0 rounded-full transition-colors ${
                step.state === "done"
                  ? "bg-[var(--forest)]"
                  : step.state === "active"
                    ? "bg-[var(--teal)] ac-pulse"
                    : "bg-[var(--rule)]"
              }`}
              aria-hidden
            />
            <span className={step.state === "pending" ? "text-[var(--ink-muted)]" : "text-[var(--ink)]"}>
              {step.label}
              {step.state === "active" ? <span className="sr-only"> (current)</span> : null}
              {step.state === "done" ? <span className="sr-only"> (done)</span> : null}
            </span>
          </li>
        ))}
      </ol>

      {failed && onRetry ? (
        <button
          type="button"
          className="ac-hit ac-press mt-5 rounded-[var(--radius-sm)] border border-[var(--rule)] bg-[var(--paper-2)] px-4 text-sm font-medium"
          onClick={onRetry}
        >
          Retry analysis
        </button>
      ) : null}
    </div>
  );
}
