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

/** Diagnostic checklist — more granular than API phases. */
const DISPLAY_STEPS: DisplayStep[] = [
  { id: "brief", label: "Analyzing Assignment Brief", match: /upload|extract|document|queued|process/i },
  { id: "thesis", label: "Evaluating Thesis", match: /thesis|structure|interpret/i },
  { id: "evidence", label: "Reviewing Evidence", match: /argument|evidence|writ|grammar|analy/i },
  { id: "alignment", label: "Checking Question Alignment", match: /question|relevance|align/i },
  { id: "citations", label: "Detecting Citation Quality", match: /citation|reference/i },
  { id: "report", label: "Assembling Diagnostic Report", match: /complet|report|scor|build|generat/i },
];

const PHASE_COPY: Record<UploadPhase, { title: string; body: string }> = {
  idle: { title: "Ready when you are", body: "Paste a draft or upload a file to begin." },
  dragging: { title: "Drop to upload", body: "Release to attach your PDF, DOCX, TXT, or MD file." },
  uploading: { title: "Receiving draft", body: "Sending your work securely for diagnosis…" },
  processing: { title: "Preparing document", body: "Extracting text and validating the file…" },
  analyzing: { title: "Running academic health scan", body: "Assessing brief fit, thesis, evidence, and citations…" },
  generating: { title: "Building your report", body: "Assembling the Academic Performance Overview…" },
  completed: { title: "Diagnosis complete", body: "Your Academic Performance Overview is ready." },
  failed: {
    title: "Analysis could not finish",
    body: "Something went wrong. Use Try again, or open your dashboard — you will not be left waiting.",
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
  if (phase === "processing") return 0;
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

  const scanning = !completed && !failed;

  return (
    <div
      className="ac-reveal ac-surface relative overflow-hidden p-5 md:p-6"
      aria-live="polite"
      aria-busy={scanning}
    >
      {scanning ? <div className="ac-scan-rail" aria-hidden /> : null}

      <div className="relative flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-sm font-semibold text-[var(--teal)]">{copy.title}</p>
          <p className="mt-1 text-sm leading-6 text-[var(--ink-muted)]">{copy.body}</p>
        </div>
        {scanning ? (
          <p className="text-xs font-medium tabular-nums text-[var(--ink-muted)]" aria-hidden>
            {progressPct}%
          </p>
        ) : null}
      </div>

      <div
        className="relative mt-4 h-1.5 overflow-hidden rounded-full bg-[var(--rule)]"
        role="progressbar"
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={progressPct}
        aria-label="Analysis progress"
      >
        <div
          className={`ac-progress-liquid h-full rounded-full ${failed ? "bg-[var(--crimson)]" : "bg-[var(--teal)]"}`}
          style={{ width: `${progressPct}%` }}
        />
      </div>

      <ol className="relative mt-5 space-y-2.5">
        {steps.map((step) => (
          <li
            key={step.id}
            className={`flex items-center gap-3 text-sm ${
              step.state === "done" ? "ac-scan-step-done" : step.state === "active" ? "ac-step-enter" : ""
            }`}
          >
            <span
              className={`grid h-5 w-5 shrink-0 place-items-center rounded-full text-[10px] font-semibold ${
                step.state === "done"
                  ? "bg-[var(--forest)] text-white"
                  : step.state === "active"
                    ? "border border-[var(--teal)] text-[var(--teal)]"
                    : "border border-[var(--rule)] text-transparent"
              }`}
              aria-hidden
            >
              {step.state === "done" ? <span className="ac-scan-check">✓</span> : step.state === "active" ? "·" : ""}
            </span>
            <span
              className={
                step.state === "pending"
                  ? "text-[var(--ink-muted)]"
                  : step.state === "done"
                    ? "text-[var(--ink)]"
                    : "font-medium text-[var(--ink)]"
              }
            >
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
          className="ac-hit ac-btn-micro ac-press mt-5 rounded-[var(--radius-sm)] border border-[var(--rule)] bg-[var(--paper-2)] px-4 text-sm font-medium"
          onClick={onRetry}
        >
          Retry analysis
        </button>
      ) : null}
    </div>
  );
}
