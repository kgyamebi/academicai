"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import { ScoreRing } from "@/components/ScoreRing";
import { ButtonLink } from "@/components/ui/Button";
import { EmptyState, Skeleton } from "@/components/ui/EmptyState";
import {
  AnimatedNumber,
  MiniRing,
  ProgressBar,
  SectionHeading,
  Sparkline,
  TrendPill,
} from "@/components/dashboard/primitives";
import { cn } from "@/lib/utils";

type Dimension = {
  category: string;
  label: string;
  score: number;
  delta: number | null;
};

type AssignmentRow = {
  id: string;
  title: string;
  status: string;
  updated_at: string | null;
  score: number | null;
  weakest_area: string | null;
  report_id: string | null;
};

type PriorityFix = {
  id: string;
  title: string;
  impact_score: number;
  estimated_improvement: string;
  time_required: string;
  category: string | null;
};

type Dash = {
  assignments: number;
  average_score: number | null;
  checks_used: number;
  checks_remaining: number;
  checks_per_month?: number;
  plan: string;
  plan_slug?: string;
  improvement_trend: number[];
  recent_reports: {
    id: string;
    score: number;
    summary: string;
    created_at: string;
    assignment_id?: string | null;
  }[];
  recent_documents: { id: string; filename: string; word_count: number }[];
  user?: {
    full_name: string;
    first_name: string;
    is_guest: boolean;
    academic_level: string | null;
  };
  report_count?: number;
  weekly_delta?: number | null;
  monthly_delta?: number | null;
  dimensions?: Dimension[];
  most_improved?: Dimension[];
  priority_fixes?: PriorityFix[];
  recent_assignments?: AssignmentRow[];
  achievements?: { id: string; title: string; earned: boolean }[];
  coach_suggestions?: { id: string; title: string; body: string }[];
  credits?: number;
  features?: Record<string, boolean>;
};

function greetingForNow() {
  const h = new Date().getHours();
  if (h < 12) return "Good morning";
  if (h < 18) return "Good afternoon";
  return "Good evening";
}

function statusLabel(status: string) {
  const map: Record<string, string> = {
    draft: "Draft",
    analyzing: "Analyzing",
    ready: "Ready",
    completed: "Completed",
  };
  return map[status] || status.replaceAll("_", " ");
}

export default function DashboardPage() {
  const [data, setData] = useState<Dash | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api<Dash>("/api/dashboard")
      .then(setData)
      .catch((e) => setError(e.message));
  }, []);

  const health = useMemo(() => {
    if (!data) return null;
    return data.average_score ?? data.recent_reports[0]?.score ?? null;
  }, [data]);

  if (error) {
    const needsAuth = /sign in|unauthorized|401|session|login/i.test(error);
    return (
      <main className="space-y-8">
        <h1 className="font-serif text-3xl md:text-4xl">Dashboard</h1>
        <section
          role="alert"
          className="ac-enter relative overflow-hidden rounded-[var(--radius-lg)] border border-[var(--rule)] bg-[var(--paper-2)]"
        >
          <div className="ac-hero-plane absolute inset-0 opacity-90" aria-hidden />
          <div className="relative grid gap-6 p-6 md:grid-cols-[1.2fr_0.8fr] md:items-center md:p-8">
            <div>
              <p className="text-sm font-medium tracking-wide text-[var(--teal)]">
                {needsAuth ? "Sign in required" : "Couldn’t load workspace"}
              </p>
              <p className="mt-2 font-serif text-2xl md:text-3xl">
                {needsAuth
                  ? "Your academic command center is ready — sign in to open it."
                  : "We hit a snag loading your dashboard."}
              </p>
              <p className="mt-3 max-w-xl text-sm leading-7 text-[var(--ink-muted)]">
                {needsAuth
                  ? "Health score, Fix-First actions, momentum charts, and coach suggestions appear after you authenticate. Guests can also start a quick check without an account."
                  : error}
              </p>
              <div className="mt-6 flex flex-wrap gap-3">
                <ButtonLink href="/login" variant="primary">
                  Sign in
                </ButtonLink>
                <ButtonLink href="/register" variant="secondary">
                  Create account
                </ButtonLink>
                <ButtonLink href="/check" variant="ghost">
                  Try a guest check
                </ButtonLink>
              </div>
            </div>
            <div className="grid gap-3 sm:grid-cols-2" aria-hidden>
              {["Academic Health", "Action Center", "Fix-First", "Momentum"].map((label) => (
                <div key={label} className="rounded-[var(--radius-md)] border border-[var(--rule)] bg-[var(--paper-2)]/80 px-4 py-4">
                  <p className="text-xs font-medium uppercase tracking-wide text-[var(--ink-muted)]">{label}</p>
                  <div className="mt-3 h-2 w-2/3 rounded-full bg-[var(--rule)]" />
                  <div className="mt-2 h-2 w-1/2 rounded-full bg-[var(--rule)]" />
                </div>
              ))}
            </div>
          </div>
        </section>
        {!needsAuth ? (
          <p className="text-sm text-[var(--ink-muted)]">
            {error}{" "}
            <Link href="/login" className="text-[var(--teal)] underline">
              Sign in
            </Link>
          </p>
        ) : null}
      </main>
    );
  }

  if (!data) {
    return (
      <main aria-busy="true">
        <h1 className="font-serif text-3xl">Dashboard</h1>
        <div className="mt-8 space-y-4">
          <Skeleton className="h-28 w-full rounded-[var(--radius-md)]" />
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {Array.from({ length: 4 }).map((_, i) => (
              <Skeleton key={i} className="h-28 rounded-[var(--radius-md)]" />
            ))}
          </div>
          <Skeleton className="h-48 w-full rounded-[var(--radius-md)]" />
          <span className="sr-only">Loading dashboard…</span>
        </div>
      </main>
    );
  }

  const name = data.user?.first_name || "Scholar";
  const greeting = greetingForNow();
  const monthly = data.monthly_delta ?? null;
  const weekly = data.weekly_delta ?? null;
  const dimensions = data.dimensions || [];
  const assignments = data.recent_assignments || [];
  const fixes = data.priority_fixes || [];
  const achievements = data.achievements || [];
  const coach = data.coach_suggestions || [];
  const features = data.features || {};
  const checksCap = data.checks_per_month ?? Math.max(data.checks_used + data.checks_remaining, 1);
  const usagePct = Math.min(100, Math.round((data.checks_used / checksCap) * 100));
  const hasWork = data.report_count ? data.report_count > 0 : data.recent_reports.length > 0;
  const continueHref = hasWork ? "/app/assignments" : "/check";
  const continueLabel = hasWork ? "Continue Improving" : "Start First Analysis";

  return (
    <main className="space-y-10 md:space-y-12">
      {/* SECTION 1 — Welcome — h1 name "Dashboard" required by a11y cert */}
      <section
        aria-labelledby="welcome-heading"
        className="ac-enter relative overflow-hidden rounded-[var(--radius-lg)] border border-[var(--rule)] bg-[var(--paper-2)]"
      >
        <div className="ac-hero-plane absolute inset-0 opacity-90" aria-hidden />
        <div className="ac-hero-grid absolute inset-0" aria-hidden />
        <div className="relative grid gap-8 p-6 md:grid-cols-[1.4fr_auto] md:items-center md:p-8">
          <div>
            <h1 id="welcome-heading" className="text-sm font-medium tracking-wide text-[var(--teal)]">
              Dashboard
            </h1>
            <p className="mt-1 text-xs font-medium uppercase tracking-wide text-[var(--ink-muted)]">
              Academic Success Workspace
            </p>
            <p className="mt-2 font-serif text-3xl leading-tight md:text-4xl" aria-live="polite">
              {greeting} {name}
            </p>
            <p className="mt-3 max-w-xl text-sm leading-7 text-[var(--ink-muted)]">
              {health != null ? (
                <>
                  Your Academic Health Score is{" "}
                  <span className="font-semibold text-[var(--ink)]">
                    <AnimatedNumber value={health} />
                  </span>
                  {monthly != null ? (
                    <>
                      {" "}
                      —{" "}
                      <span className={monthly >= 0 ? "text-[var(--forest)]" : "text-[var(--crimson)]"}>
                        {monthly >= 0 ? "+" : ""}
                        {monthly}% improvement this month
                      </span>
                    </>
                  ) : null}
                </>
              ) : (
                <>Upload a draft to unlock your Academic Health Score and a clear path forward.</>
              )}
            </p>
            <div className="mt-5 flex flex-wrap items-center gap-3">
              <span className="rounded-full border border-[var(--rule)] bg-[var(--paper-2)] px-3 py-1 text-xs font-medium text-[var(--ink-muted)]">
                Plan · {data.plan}
              </span>
              <TrendPill delta={weekly} label="this week" />
              <ButtonLink href={continueHref} variant="primary">
                {continueLabel} →
              </ButtonLink>
            </div>
          </div>
          <div className="justify-self-start md:justify-self-end">
            {health != null ? (
              <ScoreRing score={health} label="Academic Health Score" size="lg" />
            ) : (
              <div className="ac-surface max-w-xs p-5">
                <p className="font-serif text-xl">No score yet</p>
                <p className="mt-2 text-sm text-[var(--ink-muted)]">Your first check unlocks the health ring.</p>
              </div>
            )}
          </div>
        </div>
      </section>

      {/* TODAY FOCUS + CONTINUE LAST */}
      <section aria-labelledby="today-focus" className="ac-enter ac-enter-delay-1 grid gap-4 lg:grid-cols-2">
        <div className="ac-surface border-[var(--teal)]/30 p-5 md:p-6">
          <p className="text-sm font-semibold tracking-wide text-[var(--teal)]">Today Focus</p>
          <h2 id="today-focus" className="mt-2 font-serif text-2xl">
            {fixes[0]?.title || (hasWork ? "Continue your weakest area" : "Run your first analysis")}
          </h2>
          <p className="mt-3 text-sm leading-7 text-[var(--ink-muted)]">
            {fixes[0]
              ? `One recommendation only — ${fixes[0].estimated_improvement} in about ${fixes[0].time_required}.`
              : hasWork
                ? `Last analysis scored ${health ?? "—"}. Open Progress and resume the top Fix-First item.`
                : "Upload a draft to get a single clear next action."}
          </p>
          <div className="mt-5">
            <ButtonLink
              href={
                fixes[0]
                  ? `/app/coach?q=${encodeURIComponent(fixes[0].title)}`
                  : hasWork
                    ? "/app/assignments"
                    : "/check"
              }
              variant="primary"
            >
              {fixes[0] ? "Work on this" : hasWork ? "Open Progress" : "Analyze Essay"}
            </ButtonLink>
          </div>
        </div>
        <div className="ac-surface p-5 md:p-6">
          <p className="text-sm font-semibold tracking-wide text-[var(--ink-muted)]">Next recommended action</p>
          <h2 className="mt-2 font-serif text-2xl">
            {hasWork ? "Re-check after you revise" : "Start with a real assignment question"}
          </h2>
          <p className="mt-3 text-sm leading-7 text-[var(--ink-muted)]">
            {hasWork
              ? "Improvement compounds when you fix Top 3 items, then run another analysis — so you can see the lift."
              : "Paste the lecturer’s question with your draft. That context is what makes feedback academic, not generic."}
          </p>
          <div className="mt-5">
            <ButtonLink href={hasWork ? "/check" : "/sample-report"} variant="secondary">
              {hasWork ? "New analysis" : "Preview a sample report"}
            </ButtonLink>
          </div>
        </div>
      </section>

      {/* WEEKLY PROGRESS SUMMARY — retention */}
      {hasWork ? (
        <section aria-labelledby="weekly-summary" className="ac-surface p-5 md:p-6">
          <SectionHeading
            id="weekly-summary"
            title="Weekly Progress Summary"
            subtitle="You are improving — not just scanning."
          />
          <div className="mt-5 grid gap-4 sm:grid-cols-3">
            <div className="rounded-[var(--radius-sm)] border border-[var(--rule)] px-4 py-4">
              <p className="text-xs uppercase tracking-wide text-[var(--ink-muted)]">This week</p>
              <p
                className={cn(
                  "mt-2 font-serif text-3xl tabular-nums",
                  weekly == null ? "text-[var(--ink-muted)]" : weekly >= 0 ? "text-[var(--forest)]" : "text-[var(--crimson)]",
                )}
              >
                {weekly == null ? "—" : `${weekly >= 0 ? "+" : ""}${weekly}%`}
              </p>
            </div>
            <div className="rounded-[var(--radius-sm)] border border-[var(--rule)] px-4 py-4">
              <p className="text-xs uppercase tracking-wide text-[var(--ink-muted)]">Most improved</p>
              <p className="mt-2 font-medium">
                {(data.most_improved || [])[0]?.label || "Keep analyzing to unlock"}
              </p>
              {(data.most_improved || [])[0]?.delta != null ? (
                <p className="mt-1 text-sm text-[var(--forest)]">
                  +{data.most_improved![0].delta} pts
                </p>
              ) : null}
            </div>
            <div className="rounded-[var(--radius-sm)] border border-[var(--rule)] px-4 py-4">
              <p className="text-xs uppercase tracking-wide text-[var(--ink-muted)]">Essays analyzed</p>
              <p className="mt-2 font-serif text-3xl tabular-nums">{data.report_count ?? data.recent_reports.length}</p>
            </div>
          </div>
        </section>
      ) : null}

      {/* CONTINUE LAST — kept below for returning users */}
      <section aria-labelledby="continue-last" className="ac-surface p-5 md:p-6">
        <p className="text-sm font-semibold tracking-wide text-[var(--ink-muted)]">Continue last assignment</p>
        {assignments[0] ? (
          <>
            <h2 id="continue-last" className="mt-2 font-serif text-2xl">
              <Link href={`/app/assignments/${assignments[0].id}`} className="hover:underline">
                {assignments[0].title}
              </Link>
            </h2>
            <p className="mt-3 text-sm leading-7 text-[var(--ink-muted)]">
              Score {assignments[0].score ?? "—"}
              {assignments[0].weakest_area ? ` · Weakest: ${assignments[0].weakest_area}` : ""}
              {" · "}
              Recommended: {fixes[0]?.title || "Open report and apply Fix-First"}
            </p>
            <div className="mt-5 flex flex-wrap gap-2">
              <ButtonLink
                href={
                  assignments[0].report_id
                    ? `/app/assignments/${assignments[0].id}/report?report=${assignments[0].report_id}`
                    : `/app/assignments/${assignments[0].id}`
                }
                variant="primary"
              >
                Continue
              </ButtonLink>
              <ButtonLink href="/app/assignments" variant="secondary">
                All progress
              </ButtonLink>
            </div>
          </>
        ) : (
          <>
            <h2 id="continue-last" className="mt-2 font-serif text-2xl">
              No assignment yet
            </h2>
            <p className="mt-3 text-sm text-[var(--ink-muted)]">Your next check becomes the workspace you return to.</p>
            <div className="mt-5">
              <ButtonLink href="/check" variant="primary">
                Analyze Essay
              </ButtonLink>
            </div>
          </>
        )}
      </section>

      {/* SECTION 2 — Action Center */}
      <section aria-labelledby="actions-heading">
        <SectionHeading id="actions-heading" title="Action Center" subtitle="The clearest next moves." />
        <div className="mt-5 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
          <ActionCard
            href="/check"
            title="New Analysis"
            body="Run a full diagnostic on a draft or file."
            accent
          />
          <ActionCard
            href="/check"
            title="Upload Assignment"
            body="Drop a PDF or DOCX and start reviewing."
          />
          <ActionCard
            href="/app/coach"
            title="Open Mentor"
            body={features.coach ? "Mentor guidance tied to your report." : "Heuristic mentor available on the free launch."}
          />
          <ActionCard
            href={hasWork ? "/app/assignments" : "/check"}
            title="View Reports"
            body={hasWork ? "Resume the latest diagnostic report." : "Reports appear after your first check."}
          />
        </div>
      </section>

      {/* SECTION 3 — Academic Health */}
      <section aria-labelledby="health-heading" className="ac-enter ac-enter-delay-2">
        <SectionHeading
          id="health-heading"
          title="Academic Health"
          subtitle="Dimension averages across your recent analyses."
        />
        {dimensions.length === 0 ? (
          <EmptyState
            className="mt-5"
            title="Dimensions unlock after analysis"
            body="Each check scores question fit, thesis, argument, evidence, structure, writing, and citations."
            actionHref="/check"
            actionLabel="Start First Analysis"
          />
        ) : (
          <div className="mt-5 grid gap-4 lg:grid-cols-[auto_1fr]">
            <div className="ac-surface flex flex-wrap justify-center gap-5 p-5 md:justify-start">
              {dimensions.map((d) => (
                <MiniRing key={d.category} score={d.score} label={d.label} />
              ))}
            </div>
            <ul className="ac-surface divide-y divide-[var(--rule)]">
              {dimensions.map((d) => (
                <li key={`bar-${d.category}`} className="px-5 py-3.5">
                  <div className="mb-2 flex items-baseline justify-between gap-3">
                    <span className="text-sm font-medium">{d.label}</span>
                    <span className="flex items-center gap-2 text-sm tabular-nums text-[var(--ink-muted)]">
                      {d.delta != null ? (
                        <span className={d.delta >= 0 ? "text-[var(--forest)]" : "text-[var(--crimson)]"}>
                          {d.delta >= 0 ? "+" : ""}
                          {d.delta}
                        </span>
                      ) : null}
                      <span className="font-serif text-lg text-[var(--ink)]">{d.score}</span>
                    </span>
                  </div>
                  <ProgressBar value={d.score} />
                </li>
              ))}
            </ul>
          </div>
        )}
      </section>

      {/* SECTION 4 — Latest Assignments */}
      <section aria-labelledby="assignments-heading">
        <SectionHeading
          id="assignments-heading"
          title="Academic Progress"
          subtitle="Resume where you left off."
          action={
            <Link href="/app/assignments" className="text-sm font-medium text-[var(--teal)] underline-offset-4 hover:underline">
              All progress
            </Link>
          }
        />
        {assignments.length === 0 ? (
          <EmptyState
            className="mt-5"
            title="No assignments yet"
            body="Upload your first essay and receive a diagnostic evaluation in minutes — then return here to track improvement."
            actionHref="/check"
            actionLabel="Analyze Essay"
          />
        ) : (
          <div className="mt-5 overflow-hidden rounded-[var(--radius-md)] border border-[var(--rule)] bg-[var(--paper-2)]">
            <div className="hidden grid-cols-[1.4fr_0.7fr_0.9fr_0.5fr_1fr_auto] gap-3 border-b border-[var(--rule)] bg-[var(--paper)] px-4 py-2.5 text-xs font-medium uppercase tracking-wide text-[var(--ink-muted)] md:grid">
              <span>Title</span>
              <span>Status</span>
              <span>Updated</span>
              <span>Score</span>
              <span>Weakest area</span>
              <span className="sr-only">Resume</span>
            </div>
            <ul className="divide-y divide-[var(--rule)]">
              {assignments.map((a) => (
                <li
                  key={a.id}
                  className="grid gap-2 px-4 py-4 transition-colors hover:bg-black/[0.02] md:grid-cols-[1.4fr_0.7fr_0.9fr_0.5fr_1fr_auto] md:items-center md:gap-3"
                >
                  <div className="min-w-0">
                    <Link href={`/app/assignments/${a.id}`} className="font-medium hover:underline">
                      {a.title}
                    </Link>
                  </div>
                  <p className="text-sm text-[var(--ink-muted)]">
                    <span className="md:hidden">Status · </span>
                    {statusLabel(a.status)}
                  </p>
                  <p className="text-sm text-[var(--ink-muted)]">
                    <span className="md:hidden">Updated · </span>
                    {a.updated_at ? new Date(a.updated_at).toLocaleDateString() : "—"}
                  </p>
                  <p className="font-serif text-lg tabular-nums">
                    {a.score != null ? a.score : "—"}
                  </p>
                  <p className="text-sm text-[var(--ink-muted)]">{a.weakest_area || "—"}</p>
                  <div>
                    <ButtonLink
                      href={a.report_id ? `/app/assignments/${a.id}/report` : `/app/assignments/${a.id}`}
                      variant="secondary"
                      className="w-full md:w-auto"
                    >
                      Resume
                    </ButtonLink>
                  </div>
                </li>
              ))}
            </ul>
          </div>
        )}
      </section>

      {/* SECTION 5 — Priority Fixes */}
      <section aria-labelledby="fixes-heading">
        <SectionHeading
          id="fixes-heading"
          title="Priority Fixes"
          subtitle="Highest leverage improvements — timeboxed."
        />
        {fixes.length === 0 ? (
          <EmptyState
            className="mt-5"
            title="No fixes yet"
            body="After your first analysis, we’ll surface the top three weaknesses with estimated lift."
            actionHref="/check"
            actionLabel="Run an analysis"
          />
        ) : (
          <ol className="mt-5 grid gap-3 md:grid-cols-3">
            {fixes.map((fix, i) => (
              <li key={fix.id} className="ac-surface group flex flex-col p-5 transition-colors hover:border-[var(--teal)]/40">
                <span className="font-serif text-2xl text-[var(--teal)]" aria-hidden>
                  {String(i + 1).padStart(2, "0")}
                </span>
                <h3 className="mt-3 font-medium leading-snug">{fix.title}</h3>
                <dl className="mt-4 space-y-1 text-sm text-[var(--ink-muted)]">
                  <div className="flex justify-between gap-2">
                    <dt>Estimated lift</dt>
                    <dd className="font-semibold text-[var(--forest)]">{fix.estimated_improvement}</dd>
                  </div>
                  <div className="flex justify-between gap-2">
                    <dt>Time</dt>
                    <dd className="font-medium text-[var(--ink)]">{fix.time_required}</dd>
                  </div>
                  <div className="flex justify-between gap-2">
                    <dt>Impact</dt>
                    <dd className="font-medium text-[var(--ink)]">{fix.impact_score}/15</dd>
                  </div>
                </dl>
                <div className="mt-5">
                  <ButtonLink href="/app/coach" variant="secondary" className="w-full">
                    Work on this
                  </ButtonLink>
                </div>
              </li>
            ))}
          </ol>
        )}
      </section>

      {/* SECTION 6 — Improvement Momentum */}
      <section aria-labelledby="momentum-heading" className="grid gap-4 lg:grid-cols-2">
        <div className="ac-surface p-5 md:p-6">
          <SectionHeading id="momentum-heading" title="Improvement Momentum" subtitle="Progress you can feel." />
          <div className="mt-5 grid grid-cols-2 gap-4">
            <MetricStat label="Weekly progress" value={weekly} />
            <MetricStat label="Monthly progress" value={monthly} />
          </div>
          {data.improvement_trend?.length ? (
            <div className="mt-6">
              <p className="text-xs font-medium uppercase tracking-wide text-[var(--ink-muted)]">Score trend</p>
              <div className="mt-3">
                <Sparkline values={data.improvement_trend} className="h-16" />
              </div>
              <div className="mt-2 flex h-14 items-end gap-1" aria-hidden>
                {data.improvement_trend.map((v, i) => (
                  <div
                    key={`${v}-${i}`}
                    className="flex-1 rounded-t bg-[var(--teal)]/60 transition-all"
                    style={{ height: `${Math.max(10, v)}%` }}
                    title={`${v}`}
                  />
                ))}
              </div>
            </div>
          ) : (
            <p className="mt-6 text-sm text-[var(--ink-muted)]">Trends appear after two or more analyses.</p>
          )}
        </div>
        <div className="ac-surface p-5 md:p-6">
          <h3 className="font-serif text-xl">Most improved skills</h3>
          {(data.most_improved || []).length ? (
            <ul className="mt-4 space-y-3">
              {data.most_improved!.map((d) => (
                <li key={d.category} className="flex items-center justify-between gap-3 rounded-[var(--radius-sm)] border border-[var(--rule)] px-3 py-3">
                  <span className="text-sm font-medium">{d.label}</span>
                  <span className="text-sm font-semibold text-[var(--forest)]">
                    {d.delta != null && d.delta >= 0 ? "+" : ""}
                    {d.delta} pts
                  </span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="mt-4 text-sm leading-7 text-[var(--ink-muted)]">
              Re-check after applying fixes to see which skills are climbing fastest.
            </p>
          )}
        </div>
      </section>

      {/* SECTION 7 — Coach */}
      <section aria-labelledby="coach-heading" className="ac-surface overflow-hidden">
        <div className="border-b border-[var(--rule)] bg-[var(--teal-soft)]/50 px-5 py-4 md:px-6">
          <div className="flex flex-wrap items-end justify-between gap-3">
            <div>
              <h2 id="coach-heading" className="font-serif text-2xl">
                Academic Coach
              </h2>
              <p className="mt-1 text-sm text-[var(--ink-muted)]">Personalized suggestions from your weakest dimensions.</p>
            </div>
            <ButtonLink href="/app/coach" variant="primary">
              Continue with Coach
            </ButtonLink>
          </div>
        </div>
        <ul className="divide-y divide-[var(--rule)]">
          {coach.map((c) => (
            <li key={c.id} className="px-5 py-4 md:px-6">
              <p className="font-medium">{c.title}</p>
              <p className="mt-1 text-sm leading-6 text-[var(--ink-muted)]">{c.body}</p>
            </li>
          ))}
        </ul>
      </section>

      {/* SECTION 8 — Achievements */}
      <section aria-labelledby="achievements-heading">
        <SectionHeading
          id="achievements-heading"
          title="Milestones"
          subtitle="Quiet progress markers — not a game loop."
        />
        <ul className="mt-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {achievements.map((a) => (
            <li
              key={a.id}
              className={cn(
                "rounded-[var(--radius-md)] border px-4 py-4",
                a.earned
                  ? "border-[var(--teal)]/35 bg-[var(--teal-soft)]/40"
                  : "border-dashed border-[var(--rule)] bg-[var(--paper-2)] opacity-70",
              )}
            >
              <p className="text-xs font-medium uppercase tracking-wide text-[var(--ink-muted)]">
                {a.earned ? "Earned" : "Locked"}
              </p>
              <p className="mt-2 font-medium">{a.title}</p>
            </li>
          ))}
        </ul>
      </section>

      {/* SECTION 9 — Usage (free launch: no upgrade pressure) */}
      <section aria-labelledby="usage-heading" className="ac-surface p-5 md:p-6">
        <SectionHeading
          id="usage-heading"
          title="Usage Overview"
          subtitle="Free public launch — fair-use limits keep the service reliable."
        />
        <div className="mt-5 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <UsageTile label="Checks remaining" value={String(data.checks_remaining)} />
          <UsageTile label="Checks used" value={`${data.checks_used} / ${checksCap}`} />
          <UsageTile label="Credits" value={String(Math.round(data.credits ?? 0))} />
          <UsageTile label="Current plan" value={data.plan} />
        </div>
        <div className="mt-5">
          <div className="mb-2 flex justify-between text-xs text-[var(--ink-muted)]">
            <span>Monthly check usage</span>
            <span>{usagePct}%</span>
          </div>
          <ProgressBar value={usagePct} tone="var(--teal)" />
        </div>
        <div className="mt-5 flex flex-wrap gap-2">
          {(
            [
              ["Full analysis", features.full_analysis],
              ["Coach", features.coach],
              ["PDF reports", features.pdf_report],
              ["Compare drafts", features.compare],
              ["Citation verify", features.citation_verify],
            ] as const
          ).map(([label, on]) => (
            <span
              key={label}
              className={cn(
                "rounded-full border px-3 py-1 text-xs font-medium",
                on
                  ? "border-[var(--teal)]/30 bg-[var(--teal-soft)] text-[var(--forest)]"
                  : "border-[var(--rule)] text-[var(--ink-muted)]",
              )}
            >
              {label}
              {on ? "" : " · limited"}
            </span>
          ))}
        </div>
        {data.checks_remaining <= 2 ? (
          <div className="mt-5 rounded-[var(--radius-sm)] border border-[var(--teal)]/30 bg-[var(--teal-soft)]/40 px-4 py-3 text-sm leading-6">
            You have {data.checks_remaining} check{data.checks_remaining === 1 ? "" : "s"} left this period. Paid upgrades
            are paused for the free launch — pace checks carefully, or{" "}
            <Link href="/contact" className="font-medium text-[var(--teal)] underline-offset-4 hover:underline">
              contact us
            </Link>{" "}
            if you hit the limit.
          </div>
        ) : (
          <p className="mt-5 text-sm text-[var(--ink-muted)]">
            Subscriptions are disabled for this release.{" "}
            <Link href="/pricing" className="font-medium text-[var(--teal)] underline-offset-4 hover:underline">
              Free launch details
            </Link>
          </p>
        )}
      </section>

      {/* Preserve recent documents + reports as progressive disclosure */}
      {data.recent_documents.length ? (
        <section aria-labelledby="docs-heading">
          <SectionHeading id="docs-heading" title="Recent documents" />
          <ul className="mt-4 divide-y divide-[var(--rule)] overflow-hidden rounded-[var(--radius-md)] border border-[var(--rule)] bg-[var(--paper-2)]">
            {data.recent_documents.map((d) => (
              <li key={d.id} className="flex items-center justify-between gap-3 px-4 py-3 text-sm">
                <span className="truncate">{d.filename}</span>
                <span className="text-[var(--ink-muted)]">{d.word_count} words</span>
              </li>
            ))}
          </ul>
        </section>
      ) : null}

      {data.recent_reports.length ? (
        <section aria-labelledby="reports-heading">
          <SectionHeading
            id="reports-heading"
            title="Recent analyses"
            action={
              <Link href="/app/assignments" className="text-sm font-medium text-[var(--teal)] underline-offset-4 hover:underline">
                Workspace
              </Link>
            }
          />
          <ul className="mt-4 space-y-3">
            {data.recent_reports.slice(0, 4).map((r) => (
              <li key={r.id} className="ac-surface flex flex-wrap items-start justify-between gap-4 p-4">
                <div className="min-w-0">
                  <p className="font-serif text-2xl tabular-nums">{r.score}/100</p>
                  <p className="mt-1 text-sm text-[var(--ink-muted)] line-clamp-2">{r.summary}</p>
                  <p className="mt-2 text-xs text-[var(--ink-muted)]">{new Date(r.created_at).toLocaleString()}</p>
                </div>
                <ButtonLink
                  href={r.assignment_id ? `/app/assignments/${r.assignment_id}/report` : "/app/assignments"}
                  variant="secondary"
                >
                  Open report
                </ButtonLink>
              </li>
            ))}
          </ul>
        </section>
      ) : null}
    </main>
  );
}

function ActionCard({
  href,
  title,
  body,
  accent,
}: {
  href: string;
  title: string;
  body: string;
  accent?: boolean;
}) {
  return (
    <Link
      href={href}
      className={cn(
        "group rounded-[var(--radius-md)] border p-5 transition-all duration-200",
        accent
          ? "border-[var(--teal)]/40 bg-[var(--teal)] text-white shadow-[var(--shadow-1)] hover:bg-[var(--teal-2)]"
          : "border-[var(--rule)] bg-[var(--paper-2)] hover:border-[var(--teal)]/35 hover:bg-[var(--teal-soft)]/40",
      )}
    >
      <p className={cn("font-serif text-xl", accent ? "text-white" : "text-[var(--ink)]")}>{title}</p>
      <p className={cn("mt-2 text-sm leading-6", accent ? "text-white/85" : "text-[var(--ink-muted)]")}>{body}</p>
      <p className={cn("mt-4 text-sm font-medium", accent ? "text-white" : "text-[var(--teal)]")}>
        Open <span aria-hidden>→</span>
      </p>
    </Link>
  );
}

function MetricStat({ label, value }: { label: string; value: number | null | undefined }) {
  return (
    <div className="rounded-[var(--radius-sm)] border border-[var(--rule)] bg-[var(--paper)] px-3 py-3">
      <p className="text-xs font-medium uppercase tracking-wide text-[var(--ink-muted)]">{label}</p>
      <p
        className={cn(
          "mt-1 font-serif text-2xl tabular-nums",
          value == null ? "text-[var(--ink-muted)]" : value >= 0 ? "text-[var(--forest)]" : "text-[var(--crimson)]",
        )}
      >
        {value == null ? "—" : `${value >= 0 ? "+" : ""}${value}%`}
      </p>
    </div>
  );
}

function UsageTile({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-[var(--radius-sm)] border border-[var(--rule)] px-4 py-3">
      <p className="text-xs font-medium uppercase tracking-wide text-[var(--ink-muted)]">{label}</p>
      <p className="mt-2 font-serif text-2xl">{value}</p>
    </div>
  );
}
