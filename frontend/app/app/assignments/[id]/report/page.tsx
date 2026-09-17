"use client";

import { Suspense, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useParams, useSearchParams } from "next/navigation";
import { AnalysisRitual } from "@/components/AnalysisRitual";
import { CategoryAccordion } from "@/components/report/CategoryAccordion";
import { FitReportUnfold, ScoreHeatmap, SeverityBucket, categoryLabel } from "@/components/report/visuals";
import { FindingCard } from "@/components/FindingCard";
import { PriorityFixes, buildPriorityFixes } from "@/components/PriorityFixes";
import { ScoreRing } from "@/components/ScoreRing";
import { ProgressBar } from "@/components/dashboard/primitives";
import { Button, ButtonLink } from "@/components/ui/Button";
import { EmptyState, Skeleton } from "@/components/ui/EmptyState";
import { api, track } from "@/lib/api";
import { cn } from "@/lib/utils";

type Report = {
  id: string;
  assignment_id?: string | null;
  overall_score: number;
  summary: string;
  disclaimer: string;
  strengths: string[];
  weaknesses: string[];
  priority_actions: string[];
  structure_map: { key: string; label: string; status: string }[];
  question: { interpretation?: string; command_words?: string[]; required?: string[] };
  scores: { category: string; score: number; weight: number; rationale: string }[];
  findings: {
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
  }[];
  findings_total?: number;
  word_count: Record<string, number>;
  readability: { score?: number; explanation?: string };
  weakest_area: {
    category?: string;
    explanation?: string;
    how_to_improve?: string;
    example?: string;
    teaching_note?: string;
  };
  share_enabled?: boolean;
  health?: {
    level: string;
    label: string;
    confidence: string;
    improvement_potential: number;
    estimated_minutes: number;
  };
  progress?: {
    previous_score: number | null;
    current_score: number;
    improvement_pct: number | null;
    category_changes: { category: string; previous: number; current: number; delta: number }[];
    previous_report_id: string | null;
  };
  created_at?: string | null;
};

export default function ReportPage() {
  return (
    <Suspense
      fallback={
        <main aria-busy="true">
          <h1 className="font-serif text-3xl">Academic Performance Overview</h1>
          <Skeleton className="mt-8 h-40 w-full rounded-[var(--radius-md)]" />
        </main>
      }
    >
      <ReportPageInner />
    </Suspense>
  );
}

function ReportPageInner() {
  const params = useParams<{ id: string }>();
  const search = useSearchParams();
  const [report, setReport] = useState<Report | null>(null);
  const [error, setError] = useState("");
  const [tab, setTab] = useState<"overview" | "findings" | "actions">("overview");
  const [selected, setSelected] = useState<Report["findings"][number] | null>(null);
  const [mode, setMode] = useState<"explain" | "suggest" | "teach" | "example">("explain");
  const [shareMsg, setShareMsg] = useState("");
  const [versionMsg, setVersionMsg] = useState("");
  const [busyShare, setBusyShare] = useState(false);
  const [busyVersion, setBusyVersion] = useState(false);
  const [overallDisplay, setOverallDisplay] = useState(0);
  const reportId = search.get("report");
  const assignmentId = params.id;

  useEffect(() => {
    if (!reportId) {
      setError("Missing report id.");
      return;
    }
    api<Report>(`/api/reports/${reportId}`)
      .then((r) => {
        setReport(r);
        track("report_viewed", "/app/report");
      })
      .catch((e) => setError(e instanceof Error ? e.message : "Could not load report"));
  }, [reportId]);

  const priorities = useMemo(() => {
    if (!report) return [];
    return buildPriorityFixes(report.priority_actions, report.scores, report.findings);
  }, [report]);

  const buckets = useMemo(() => {
    const findings = report?.findings || [];
    return {
      critical: findings.filter((f) => f.severity === "critical" || f.severity === "high"),
      important: findings.filter((f) => f.severity === "medium"),
      minor: findings.filter((f) => f.severity === "low" || f.severity === "informational"),
    };
  }, [report]);

  const selectedText = useMemo(() => {
    if (!selected) return "";
    if (mode === "suggest") return selected.suggestion;
    if (mode === "teach") {
      return selected.teaching_note || "This finding is about academic writing quality, not a hidden lecturer rule.";
    }
    if (mode === "example") {
      return selected.example || "Example: turn 'This essay is about X' into a contestable claim that answers the question.";
    }
    return selected.explanation;
  }, [selected, mode]);

  const health = report?.health;
  const progress = report?.progress;
  const projected = report
    ? Math.min(100, report.overall_score + (health?.improvement_potential || priorities.reduce((a, p) => a + p.liftPoints, 0) / 2 || 0))
    : 0;

  if (error) {
    return (
      <main>
        <h1 className="font-serif text-3xl">Academic Performance Overview</h1>
        <p role="alert" className="mt-4 text-[var(--crimson)]">
          {error}
        </p>
        <Link href={`/app/assignments/${assignmentId}`} className="mt-4 inline-block text-[var(--teal)] underline">
          Back to assignment
        </Link>
      </main>
    );
  }

  if (!report) {
    return (
      <main aria-busy="true">
        <h1 className="font-serif text-3xl">Academic Performance Overview</h1>
        <div className="mt-8 space-y-4">
          <AnalysisRitual stage="building_report" status="loading" />
          <Skeleton className="h-40 w-full rounded-[var(--radius-md)]" />
          <Skeleton className="h-24 w-full rounded-[var(--radius-md)]" />
          <span className="sr-only">Loading analysis results…</span>
        </div>
      </main>
    );
  }

  // Capture after null guard — nested async fns don't keep TS narrowing on `report`.
  const currentReport = report;

  async function downloadPdf() {
    const blob = await api<Blob>(`/api/reports/${currentReport.id}/pdf`);
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "academiccheck-report.pdf";
    a.click();
    URL.revokeObjectURL(url);
  }

  async function shareReport() {
    setBusyShare(true);
    setShareMsg("");
    try {
      const data = await api<{ path: string; expires_at: string }>(`/api/reports/${currentReport.id}/share`, {
        method: "POST",
        body: JSON.stringify({ hours: 72 }),
      });
      const url = `${window.location.origin}${data.path}`;
      await navigator.clipboard.writeText(url);
      setShareMsg("Share link copied — expires in 72 hours.");
      track("report_shared", "/app/report");
    } catch (e) {
      setShareMsg(e instanceof Error ? e.message : "Could not create share link.");
    } finally {
      setBusyShare(false);
    }
  }

  async function saveVersion() {
    setBusyVersion(true);
    setVersionMsg("");
    try {
      await api(`/api/assignments/${assignmentId}/versions`, {
        method: "POST",
        body: JSON.stringify({
          name: `After analysis ${new Date().toLocaleDateString()}`,
          notes: `Saved from report ${currentReport.id} (score ${currentReport.overall_score}).`,
        }),
      });
      setVersionMsg("Version saved to this assignment.");
      track("version_saved", "/app/report");
    } catch (e) {
      setVersionMsg(e instanceof Error ? e.message : "Could not save version.");
    } finally {
      setBusyVersion(false);
    }
  }

  function focusFix(category?: string) {
    const match =
      currentReport.findings.find((f) => f.category === category) ||
      currentReport.findings.find((f) => f.category === currentReport.weakest_area.category) ||
      currentReport.findings[0];
    setSelected(match || null);
    setTab("actions");
  }

  function scrollToFindings(id: string) {
    const f = currentReport.findings.find((x) => x.id === id);
    if (f) {
      setSelected(f);
      setTab("findings");
    }
  }

  const coachBase = `/app/coach?assignment=${assignmentId}`;

  const ActionPanel = (
    <aside className="ac-surface space-y-3 p-5 lg:sticky lg:top-6" aria-label="Report actions">
      <h2 className="font-serif text-xl">Coach Guidance</h2>
      <p className="text-sm leading-6 text-[var(--ink-muted)]">
        Ask the coach about Top 3 Critical Fixes, export a PDF, share, or re-check — without leaving this result.
      </p>
      <ButtonLink href={`${coachBase}&q=${encodeURIComponent("Help me fix the highest-priority issues in this draft.")}`} variant="primary" className="w-full">
        Improve with Mentor
      </ButtonLink>
      <Button type="button" variant="secondary" className="w-full" onClick={downloadPdf}>
        Download PDF
      </Button>
      <Button type="button" variant="secondary" className="w-full" busy={busyShare} onClick={shareReport}>
        Share Report
      </Button>
      <Button type="button" variant="secondary" className="w-full" busy={busyVersion} onClick={saveVersion}>
        Save Version
      </Button>
      <ButtonLink href={`/app/assignments/${assignmentId}/check`} variant="ghost" className="w-full border border-[var(--rule)]">
        Run New Analysis
      </ButtonLink>
      {shareMsg ? (
        <p role="status" className="text-xs leading-5 text-[var(--ink-muted)]">
          {shareMsg}
        </p>
      ) : null}
      {versionMsg ? (
        <p role="status" className="text-xs leading-5 text-[var(--ink-muted)]">
          {versionMsg}
        </p>
      ) : null}

      {(selected || report.weakest_area.category) && (
        <div className="mt-4 border-t border-[var(--rule)] pt-4">
          <h3 className="font-serif text-lg">
            {selected ? selected.location : categoryLabel(report.weakest_area.category || "weakest")}
          </h3>
          <div className="mt-3 flex flex-wrap gap-2" role="group" aria-label="Teaching modes">
            {(["explain", "suggest", "teach", "example"] as const).map((m) => (
              <button
                key={m}
                type="button"
                aria-pressed={mode === m}
                onClick={() => setMode(m)}
                className={cn(
                  "ac-hit rounded-[var(--radius-sm)] px-3 text-sm",
                  mode === m ? "bg-[var(--teal)] text-white" : "border border-[var(--rule)]",
                )}
              >
                {m === "teach" ? "Teach me" : m[0].toUpperCase() + m.slice(1)}
              </button>
            ))}
          </div>
          <p className="mt-4 text-sm leading-7 text-[var(--ink)]">
            {selectedText || report.weakest_area.how_to_improve || report.weakest_area.explanation}
          </p>
          {selected?.original_text ? (
            <blockquote className="mt-4 border-l-2 border-[var(--teal)] pl-3 text-sm italic text-[var(--ink-muted)]">
              {selected.original_text}
            </blockquote>
          ) : null}
          <Link
            href={`${coachBase}&q=${encodeURIComponent(`Help me with: ${selected?.explanation || report.weakest_area.category || "my weakest area"}`)}`}
            className="mt-4 inline-flex text-sm font-medium text-[var(--teal)] underline-offset-4 hover:underline"
          >
            Ask Coach about this →
          </Link>
        </div>
      )}
    </aside>
  );

  return (
    <main className="space-y-8 pb-28 lg:pb-8">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="text-sm font-medium tracking-wide text-[var(--teal)]">Academic Performance Overview</p>
          <h1 className="mt-2 font-serif text-3xl md:text-4xl">Academic Performance Overview</h1>
        </div>
        <div className="hidden flex-wrap gap-2 lg:flex">
          <Button type="button" variant="secondary" onClick={downloadPdf}>
            Download PDF
          </Button>
          <Button type="button" variant="primary" onClick={() => focusFix()}>
            Fix weakest area
          </Button>
        </div>
      </div>

      {/* Mobile section tabs */}
      <div className="flex gap-2 lg:hidden" role="tablist" aria-label="Report sections">
        {(
          [
            ["overview", "Overview"],
            ["findings", "Findings"],
            ["actions", "Actions"],
          ] as const
        ).map(([id, label]) => (
          <button
            key={id}
            type="button"
            role="tab"
            aria-selected={tab === id}
            onClick={() => setTab(id)}
            className={cn(
              "ac-hit rounded-[var(--radius-sm)] px-3 text-sm",
              tab === id ? "bg-[var(--teal)] text-white" : "border border-[var(--rule)] bg-[var(--paper-2)]",
            )}
          >
            {label}
          </button>
        ))}
      </div>

      <div className="grid gap-8 lg:grid-cols-[minmax(0,1fr)_300px]">
        <div className={cn("space-y-8", tab === "actions" && "hidden lg:block")}>
          {/* TOP — Performance Overview */}
          <section
            aria-labelledby="perf-heading"
            className={cn(
              "ac-reveal relative overflow-hidden rounded-[var(--radius-lg)] border border-[var(--rule)] bg-[var(--paper-2)]",
              tab === "findings" && "hidden lg:block",
            )}
          >
            <div className="ac-hero-plane absolute inset-0 opacity-80" aria-hidden />
            <div className="relative grid gap-6 p-6 md:grid-cols-[auto_1fr] md:items-center md:p-8">
              <ScoreRing
                score={report.overall_score}
                label="Academic Health Score"
                size="lg"
                compactLabel
                playKey={report.id}
                onDisplayChange={setOverallDisplay}
              />
              <div>
                <p id="perf-heading" className="font-serif text-4xl tabular-nums tracking-tight md:text-5xl">
                  <span className="inline-block tabular-nums">{overallDisplay}</span>{" "}
                  <span className="text-xl font-normal text-[var(--ink-muted)] md:text-2xl">Overall Score</span>
                </p>
                <p className="mt-2 text-lg font-medium text-[var(--teal)]">
                  {health?.label || (report.overall_score >= 75 ? "Strong Draft" : "Developing Draft")}
                </p>
                <p className="mt-2 inline-flex rounded-full border border-[var(--rule)] bg-[var(--paper-2)] px-3 py-1 text-sm font-medium">
                  Submission readiness:{" "}
                  <span className="ml-1 text-[var(--ink)]">
                    {report.overall_score >= 85
                      ? "Ready To Review"
                      : report.overall_score >= 70
                        ? "Strong Draft"
                        : report.overall_score >= 55
                          ? "Almost Ready"
                          : "Needs Work"}
                  </span>
                </p>
                <p className="mt-3 max-w-2xl text-sm leading-7 text-[var(--ink)] line-clamp-3">{report.summary}</p>
                <dl className="mt-5 grid gap-3 sm:grid-cols-3">
                  <div className="rounded-[var(--radius-sm)] border border-[var(--rule)] bg-[var(--paper-2)] px-3 py-3">
                    <dt className="text-xs uppercase tracking-wide text-[var(--ink-muted)]">Confidence</dt>
                    <dd className="mt-1 font-medium">{health?.confidence || "Moderate"}</dd>
                  </div>
                  <div className="rounded-[var(--radius-sm)] border border-[var(--rule)] bg-[var(--paper-2)] px-3 py-3">
                    <dt className="text-xs uppercase tracking-wide text-[var(--ink-muted)]">Improvement potential</dt>
                    <dd className="mt-1 font-serif text-xl text-[var(--forest)]">
                      +{health?.improvement_potential ?? priorities[0]?.liftPoints ?? 8}
                    </dd>
                  </div>
                  <div className="rounded-[var(--radius-sm)] border border-[var(--rule)] bg-[var(--paper-2)] px-3 py-3">
                    <dt className="text-xs uppercase tracking-wide text-[var(--ink-muted)]">Time to improve</dt>
                    <dd className="mt-1 font-medium">{health?.estimated_minutes ?? 20} minutes</dd>
                  </div>
                </dl>
                <p className="mt-4 text-xs leading-6 text-[var(--ink-muted)]">{report.disclaimer}</p>
              </div>
            </div>
          </section>

          {/* FIX-FIRST — answer "what next?" within 3 seconds */}
          <div className={cn("ac-reveal", tab === "findings" && "hidden lg:block")}>
            <PriorityFixes
              items={priorities}
              onFix={(item) => focusFix(item.category)}
              coachHref={(item) =>
                `${coachBase}&q=${encodeURIComponent(`Help me: ${item.title}. ${item.why}`)}`
              }
            />
          </div>

          {/* Submission Readiness — explicit section */}
          <section
            aria-labelledby="readiness-heading"
            className={cn("ac-reveal ac-surface p-5 md:p-6", tab === "findings" && "hidden lg:block")}
          >
            <h2 id="readiness-heading" className="font-serif text-2xl">
              Submission Readiness
            </h2>
            <p className="mt-2 text-lg font-medium text-[var(--teal)]">
              {report.overall_score >= 85
                ? "Ready To Review"
                : report.overall_score >= 70
                  ? "Strong Draft"
                  : report.overall_score >= 55
                    ? "Almost Ready"
                    : "Needs Work"}
            </p>
            <p className="mt-2 text-sm leading-7 text-[var(--ink-muted)]">
              {report.overall_score >= 85
                ? "This draft is in good shape for a final review pass — apply the Top 3 Critical Fixes, then proofread."
                : report.overall_score >= 70
                  ? "Solid foundation. Closing the Top 3 Critical Fixes should move you closer to submission confidence."
                  : report.overall_score >= 55
                    ? "Not submission-ready yet. Focus on the first Critical Fix before polishing language."
                    : "Priority is structural: fix the Biggest Improvement Opportunity and Top 3 items before sentence-level polish."}
            </p>
            <div className="mt-4 flex flex-wrap gap-2">
              <Button type="button" variant="primary" onClick={() => focusFix()}>
                Fix weakest area
              </Button>
              <ButtonLink href={`${coachBase}&q=${encodeURIComponent("Help me reach submission readiness.")}`} variant="secondary">
                Ask mentor
              </ButtonLink>
            </div>
          </section>

          {/* KEY FINDINGS — secondary */}
          <section aria-labelledby="key-findings-heading" className={cn(tab === "overview" && "lg:block", tab === "findings" ? "block" : "hidden lg:block")}>
            <h2 id="key-findings-heading" className="font-serif text-2xl">
              Key findings
            </h2>
            <p className="mt-1 text-sm text-[var(--ink-muted)]">Prioritized so you know what to fix first.</p>
            <div className="mt-5 grid gap-4 lg:grid-cols-3">
              <SeverityBucket
                title="Critical"
                tone="critical"
                items={buckets.critical}
                empty="No critical findings — breathe."
                onSelect={scrollToFindings}
              />
              <SeverityBucket
                title="Important"
                tone="important"
                items={buckets.important}
                empty="No medium-priority findings."
                onSelect={scrollToFindings}
              />
              <SeverityBucket
                title="Minor"
                tone="minor"
                items={buckets.minor}
                empty="No minor notes."
                onSelect={scrollToFindings}
              />
            </div>
          </section>

          {/* Category scores table stays visible for a11y certification */}
          <section aria-labelledby="viz-heading" className={cn("space-y-6", tab === "findings" && "hidden lg:block")}>
            <div>
              <h2 id="viz-heading" className="font-serif text-2xl">
                Category scores
              </h2>
              <p className="mt-1 text-sm text-[var(--ink-muted)]">Exact scores — expand below for charts and deeper review.</p>
            </div>
            <div className="overflow-x-auto rounded-[var(--radius-md)] border border-[var(--rule)] bg-[var(--paper-2)]">
              <table className="w-full min-w-[28rem] text-left text-sm" aria-label="Category scores">
                <caption className="border-b border-[var(--rule)] px-4 py-3 text-left font-serif text-lg text-[var(--ink)]">
                  Category scores
                </caption>
                <thead>
                  <tr className="border-b border-[var(--rule)] text-xs uppercase tracking-wide text-[var(--ink-muted)]">
                    <th scope="col" className="px-4 py-2 font-medium">
                      Category
                    </th>
                    <th scope="col" className="px-4 py-2 font-medium">
                      Score
                    </th>
                    <th scope="col" className="px-4 py-2 font-medium">
                      Rationale
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {report.scores.map((s) => (
                    <tr key={s.category} className="border-b border-[var(--rule)] last:border-0">
                      <th scope="row" className="px-4 py-3 font-medium">
                        {categoryLabel(s.category)}
                      </th>
                      <td className="px-4 py-3 font-serif text-lg tabular-nums">{s.score}</td>
                      <td className="px-4 py-3 text-[var(--ink-muted)]">{s.rationale}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>

          <details className={cn("ac-surface group", tab === "findings" && "hidden lg:block")}>
            <summary className="cursor-pointer list-none px-5 py-4 font-serif text-xl [&::-webkit-details-marker]:hidden">
              <span className="flex items-center justify-between gap-3">
                Charts & deeper analysis
                <span className="text-sm font-sans font-normal text-[var(--teal)]">Optional</span>
              </span>
            </summary>
            <div className="space-y-8 border-t border-[var(--rule)] px-5 py-6">
              <FitReportUnfold
                question={report.question?.interpretation}
                fitScore={
                  report.scores.find((s) => s.category === "relevance")?.score ??
                  Math.round(report.overall_score * 0.95)
                }
                concepts={[
                  ...(report.question?.command_words || []),
                  ...(report.question?.required || []).slice(0, 4),
                ].slice(0, 6)}
                scores={report.scores}
              />
              <ScoreHeatmap scores={report.scores} />
            </div>
          </details>

          {/* BEFORE / AFTER */}
          <section aria-labelledby="before-after-heading" className={cn("ac-surface p-5 md:p-6", tab !== "overview" && "hidden lg:block")}>
            <h2 id="before-after-heading" className="font-serif text-2xl">
              Before / after preview
            </h2>
            <p className="mt-1 text-sm text-[var(--ink-muted)]">What focused fixes can unlock on the next check.</p>
            <div className="mt-5 grid gap-4 sm:grid-cols-2">
              <div className="rounded-[var(--radius-md)] border border-[var(--rule)] bg-[var(--paper)] p-4">
                <p className="text-xs font-semibold uppercase tracking-wide text-[var(--ink-muted)]">Current situation</p>
                <p className="mt-2 font-serif text-4xl tabular-nums">{report.overall_score}</p>
                <p className="mt-2 text-sm leading-6 text-[var(--ink-muted)]">
                  {health?.label || "Current diagnostic health"} — fix the top three actions above first.
                </p>
                <div className="mt-4">
                  <ProgressBar value={report.overall_score} />
                </div>
              </div>
              <div className="rounded-[var(--radius-md)] border border-[var(--teal)]/35 bg-[var(--teal-soft)]/40 p-4">
                <p className="text-xs font-semibold uppercase tracking-wide text-[var(--teal)]">Improved situation</p>
                <p className="mt-2 font-serif text-4xl tabular-nums text-[var(--forest)]">{Math.round(projected)}</p>
                <p className="mt-2 text-sm leading-6 text-[var(--ink)]">
                  Estimated after completing Fix-First actions (~{health?.estimated_minutes ?? 20} min).
                </p>
                <div className="mt-4">
                  <ProgressBar value={projected} tone="var(--forest)" />
                </div>
              </div>
            </div>
          </section>

          {/* PROGRESS ENGINE */}
          <section aria-labelledby="progress-heading" className={cn("ac-surface p-5 md:p-6", tab !== "overview" && "hidden lg:block")}>
            <h2 id="progress-heading" className="font-serif text-2xl">
              Academic Progress
            </h2>
            <div className="mt-4 grid gap-4 sm:grid-cols-3">
              <div className="rounded-[var(--radius-sm)] border border-[var(--rule)] px-3 py-3">
                <p className="text-xs uppercase tracking-wide text-[var(--ink-muted)]">Previous analysis</p>
                <p className="mt-1 font-serif text-2xl tabular-nums">
                  {progress?.previous_score != null ? progress.previous_score : "—"}
                </p>
              </div>
              <div className="rounded-[var(--radius-sm)] border border-[var(--rule)] px-3 py-3">
                <p className="text-xs uppercase tracking-wide text-[var(--ink-muted)]">Current analysis</p>
                <p className="mt-1 font-serif text-2xl tabular-nums">{progress?.current_score ?? report.overall_score}</p>
              </div>
              <div className="rounded-[var(--radius-sm)] border border-[var(--rule)] px-3 py-3">
                <p className="text-xs uppercase tracking-wide text-[var(--ink-muted)]">Improvement</p>
                <p
                  className={cn(
                    "mt-1 font-serif text-2xl tabular-nums",
                    progress?.improvement_pct == null
                      ? "text-[var(--ink-muted)]"
                      : progress.improvement_pct >= 0
                        ? "text-[var(--forest)]"
                        : "text-[var(--crimson)]",
                  )}
                >
                  {progress?.improvement_pct == null
                    ? "First check"
                    : `${progress.improvement_pct >= 0 ? "+" : ""}${progress.improvement_pct}%`}
                </p>
              </div>
            </div>
            {(progress?.category_changes || []).length ? (
              <ul className="mt-5 space-y-2">
                {progress!.category_changes.map((c) => (
                  <li key={c.category} className="flex items-center justify-between gap-3 text-sm">
                    <span>{categoryLabel(c.category)}</span>
                    <span className="tabular-nums text-[var(--ink-muted)]">
                      {c.previous} → {c.current}{" "}
                      <span className={c.delta >= 0 ? "text-[var(--forest)]" : "text-[var(--crimson)]"}>
                        ({c.delta >= 0 ? "+" : ""}
                        {c.delta})
                      </span>
                    </span>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="mt-4 text-sm text-[var(--ink-muted)]">
                Re-check after revisions to unlock category-by-category growth, plus weekly and monthly trends on your dashboard.
              </p>
            )}
            <div className="mt-4 flex flex-wrap gap-3 text-sm">
              <Link href="/app/dashboard" className="font-medium text-[var(--teal)] underline-offset-4 hover:underline">
                Weekly & monthly growth on dashboard
              </Link>
              {progress?.previous_report_id ? (
                <Link
                  href={`/app/assignments/${assignmentId}/report?report=${progress.previous_report_id}`}
                  className="font-medium text-[var(--teal)] underline-offset-4 hover:underline"
                >
                  Open previous analysis
                </Link>
              ) : null}
            </div>
          </section>

          {/* CATEGORY ANALYSIS */}
          <section aria-labelledby="categories-heading" className={cn(tab !== "overview" && "hidden lg:block")}>
            <h2 id="categories-heading" className="font-serif text-2xl">
              Detailed Analysis
            </h2>
            <p className="mt-1 text-sm text-[var(--ink-muted)]">Expand any dimension — strengths, weaknesses, examples, coach.</p>
            <div className="mt-5">
              <CategoryAccordion
                scores={report.scores}
                findings={report.findings}
                strengths={report.strengths}
                weaknesses={report.weaknesses}
                assignmentId={assignmentId}
              />
            </div>
          </section>

          {/* Biggest improvement + strengths / weaknesses */}
          {report.weakest_area?.category || report.weakest_area?.explanation ? (
            <section
              aria-labelledby="opportunity-heading"
              className={cn("ac-surface p-5 md:p-6", tab !== "overview" && "hidden lg:block")}
            >
              <h2 id="opportunity-heading" className="font-serif text-2xl">
                Biggest Improvement Opportunity
              </h2>
              <p className="mt-2 text-sm font-medium text-[var(--teal)]">
                {report.weakest_area.category
                  ? categoryLabel(report.weakest_area.category)
                  : "Focus area"}
              </p>
              <p className="mt-2 text-sm leading-7 text-[var(--ink)]">
                {report.weakest_area.explanation || "This is the dimension with the most room to lift your score."}
              </p>
              {report.weakest_area.how_to_improve ? (
                <p className="mt-3 text-sm leading-7 text-[var(--ink-muted)]">{report.weakest_area.how_to_improve}</p>
              ) : null}
            </section>
          ) : null}

          <div className={cn("grid gap-6 md:grid-cols-2", tab !== "overview" && "hidden lg:grid")}>
            <div className="ac-surface p-5">
              <h3 className="font-serif text-xl">Key Strengths</h3>
              {report.strengths.length ? (
                <ul className="mt-3 list-disc space-y-2 pl-5 text-sm leading-6">
                  {report.strengths.map((s) => (
                    <li key={s}>{s}</li>
                  ))}
                </ul>
              ) : (
                <p className="mt-3 text-sm text-[var(--ink-muted)]">No highlighted strengths yet.</p>
              )}
            </div>
            <div className="ac-surface p-5">
              <h3 className="font-serif text-xl">Key Weaknesses</h3>
              {report.weaknesses.length ? (
                <ul className="mt-3 list-disc space-y-2 pl-5 text-sm leading-6">
                  {report.weaknesses.map((s) => (
                    <li key={s} className="flex flex-wrap items-baseline justify-between gap-2">
                      <span>{s}</span>
                      <Link
                        href={`${coachBase}&q=${encodeURIComponent(`Help me address: ${s}`)}`}
                        className="shrink-0 text-xs font-medium text-[var(--teal)] underline-offset-4 hover:underline"
                      >
                        Ask Coach
                      </Link>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="mt-3 text-sm text-[var(--ink-muted)]">No major weaknesses flagged.</p>
              )}
            </div>
          </div>

          {report.structure_map?.length ? (
            <div className={cn(tab !== "overview" && "hidden lg:block")}>
              <h2 className="font-serif text-2xl">Structure map</h2>
              <ul className="mt-4 divide-y divide-[var(--rule)] overflow-hidden rounded-[var(--radius-md)] border border-[var(--rule)] bg-[var(--paper-2)]">
                {report.structure_map.map((s) => (
                  <li key={s.key} className="flex items-center justify-between gap-3 px-4 py-3 text-sm">
                    <span>{s.label}</span>
                    <span className="text-[var(--ink-muted)] capitalize">{s.status}</span>
                  </li>
                ))}
              </ul>
            </div>
          ) : null}

          {/* DETAILED FINDINGS */}
          <section
            aria-labelledby="findings-list-heading"
            className={cn("space-y-4", tab === "overview" && "lg:block", tab === "findings" ? "block" : "hidden lg:block")}
          >
            <div className="flex items-end justify-between gap-3">
              <h2 id="findings-list-heading" className="font-serif text-2xl">
                Detailed findings
              </h2>
              <Link href={coachBase} className="text-sm font-medium text-[var(--teal)] underline-offset-4 hover:underline">
                Open coach
              </Link>
            </div>
            {report.findings.length === 0 ? (
              <EmptyState title="No findings listed" body="This report did not return detailed findings for this page." />
            ) : (
              report.findings.map((f) => (
                <FindingCard
                  key={f.id}
                  finding={f}
                  onSelect={() => {
                    setSelected(f);
                    setTab("actions");
                  }}
                />
              ))
            )}
          </section>
        </div>

        {/* Sticky action rail — desktop always; mobile via Actions tab */}
        <div className={cn(tab === "actions" ? "block" : "hidden lg:block")}>{ActionPanel}</div>
      </div>

      {/* Mobile sticky next-action bar */}
      <div className="fixed inset-x-0 bottom-[calc(3.5rem+env(safe-area-inset-bottom))] z-30 border-t border-[var(--rule)] bg-[var(--paper-2)]/95 px-4 py-3 backdrop-blur lg:hidden">
        <div className="mx-auto flex max-w-lg gap-2">
          <Button type="button" variant="primary" className="flex-1" onClick={() => focusFix()}>
            Fix first priority
          </Button>
          <ButtonLink href={`${coachBase}&q=${encodeURIComponent(priorities[0]?.title || "Help me improve this draft")}`} variant="secondary" className="flex-1">
            Mentor
          </ButtonLink>
        </div>
      </div>
    </main>
  );
}
