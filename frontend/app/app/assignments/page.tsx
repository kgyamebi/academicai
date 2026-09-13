"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import { ButtonLink } from "@/components/ui/Button";
import { EmptyState, Skeleton } from "@/components/ui/EmptyState";
import { cn } from "@/lib/utils";

type Assignment = {
  id: string;
  title: string;
  academic_level: string;
  citation_style: string;
  updated_at?: string;
  created_at?: string;
  latest_score?: number | null;
  best_score?: number | null;
  previous_score?: number | null;
  improvement_delta?: number | null;
  weakest_area?: string | null;
  last_analysis_at?: string | null;
  latest_report_id?: string | null;
  score_timeline?: number[];
};

export default function AssignmentsPage() {
  const [items, setItems] = useState<Assignment[] | null>(null);

  useEffect(() => {
    api<{ items: Assignment[] }>("/api/assignments")
      .then((d) => setItems(d.items || []))
      .catch(() => setItems([]));
  }, []);

  if (items === null) {
    return (
      <main aria-busy="true">
        <h1 className="font-serif text-3xl">Academic Progress</h1>
        <div className="mt-8 space-y-3">
          <Skeleton className="h-28 w-full" />
          <Skeleton className="h-28 w-full" />
        </div>
      </main>
    );
  }

  return (
    <main className="space-y-8">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="text-sm font-medium tracking-wide text-[var(--teal)]">Workspace</p>
          <h1 className="mt-2 font-serif text-3xl md:text-4xl">Academic Progress</h1>
          <p className="mt-2 max-w-xl text-sm leading-7 text-[var(--ink-muted)]">
            Where you are, what improved, and what to continue — not a file dump.
          </p>
        </div>
        <ButtonLink href="/check" variant="primary">
          New analysis
        </ButtonLink>
      </div>

      {items.length === 0 ? (
        <EmptyState
          className="mt-8"
          kicker="Get started"
          title="Upload your first essay"
          body="Receive an Academic Performance Overview in minutes — Top 3 Critical Fixes, readiness, and a clear next step. Progress tracking unlocks after your first analysis."
          actionHref="/check"
          actionLabel="Analyze Essay"
        />
      ) : (
        <ul className="space-y-4">
          {items.map((a) => {
            const delta = a.improvement_delta;
            const before = a.previous_score;
            const after = a.latest_score;
            const reportHref = a.latest_report_id
              ? `/app/assignments/${a.id}/report?report=${a.latest_report_id}`
              : `/app/assignments/${a.id}`;
            return (
              <li key={a.id} className="ac-surface overflow-hidden">
                <div className="grid gap-5 p-5 md:grid-cols-[1.2fr_auto] md:items-center md:p-6">
                  <div className="min-w-0">
                    <Link href={`/app/assignments/${a.id}`} className="font-serif text-xl hover:underline">
                      {a.title}
                    </Link>
                    <p className="mt-1 text-sm text-[var(--ink-muted)]">
                      {a.academic_level.replaceAll("_", " ")} · {a.citation_style.toUpperCase()}
                      {a.last_analysis_at
                        ? ` · Last analysis ${new Date(a.last_analysis_at).toLocaleDateString()}`
                        : " · No analysis yet"}
                    </p>
                    {a.weakest_area ? (
                      <p className="mt-2 text-sm">
                        Weakest area: <span className="font-medium">{a.weakest_area}</span>
                      </p>
                    ) : null}

                    {before != null && after != null ? (
                      <div className="mt-4 flex flex-wrap items-end gap-4">
                        <div>
                          <p className="text-[11px] uppercase tracking-wide text-[var(--ink-muted)]">Before</p>
                          <p className="font-serif text-2xl tabular-nums text-[var(--ink-muted)]">{before}</p>
                        </div>
                        <div>
                          <p className="text-[11px] uppercase tracking-wide text-[var(--ink-muted)]">After</p>
                          <p className="font-serif text-3xl tabular-nums">{after}</p>
                        </div>
                        {delta != null ? (
                          <p
                            className={cn(
                              "font-serif text-2xl tabular-nums",
                              delta >= 0 ? "text-[var(--forest)]" : "text-[var(--crimson)]",
                            )}
                          >
                            {delta >= 0 ? "+" : ""}
                            {delta}
                          </p>
                        ) : null}
                      </div>
                    ) : after != null ? (
                      <p className="mt-4 font-serif text-3xl tabular-nums">
                        {after}
                        <span className="ml-2 text-sm font-sans text-[var(--ink-muted)]">latest score</span>
                      </p>
                    ) : null}

                    {a.score_timeline && a.score_timeline.length > 1 ? (
                      <div className="mt-4" aria-label="Improvement timeline">
                        <p className="text-[11px] uppercase tracking-wide text-[var(--ink-muted)]">
                          Writing quality progression
                        </p>
                        <div className="mt-2 flex h-12 items-end gap-1.5" aria-hidden>
                          {a.score_timeline.map((v, i) => (
                            <div key={`${a.id}-${i}`} className="flex flex-1 flex-col items-center gap-1">
                              <div
                                className="w-full rounded-t bg-[var(--teal)]/55"
                                style={{ height: `${Math.max(12, v)}%` }}
                                title={`${v}`}
                              />
                              <span className="text-[10px] tabular-nums text-[var(--ink-muted)]">{v}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    ) : null}

                    <dl className="mt-4 flex flex-wrap gap-x-5 gap-y-1 text-xs text-[var(--ink-muted)]">
                      <div>
                        <dt className="inline">Latest · </dt>
                        <dd className="inline tabular-nums">{a.latest_score ?? "—"}</dd>
                      </div>
                      <div>
                        <dt className="inline">Best · </dt>
                        <dd className="inline tabular-nums">{a.best_score ?? "—"}</dd>
                      </div>
                    </dl>
                  </div>
                  <div className="flex flex-col gap-2 md:items-stretch">
                    <ButtonLink href={reportHref} variant="primary" className="justify-center">
                      {a.latest_report_id ? "Continue improving" : "Open workspace"}
                    </ButtonLink>
                    {a.latest_report_id ? (
                      <ButtonLink href={reportHref} variant="secondary" className="justify-center">
                        View report
                      </ButtonLink>
                    ) : (
                      <ButtonLink href={`/app/assignments/${a.id}/check`} variant="secondary" className="justify-center">
                        Run analysis
                      </ButtonLink>
                    )}
                  </div>
                </div>
              </li>
            );
          })}
        </ul>
      )}
    </main>
  );
}
