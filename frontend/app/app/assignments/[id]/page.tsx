"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { api } from "@/lib/api";
import { ButtonLink } from "@/components/ui/Button";
import { EmptyState, SkeletonBlock } from "@/components/ui/EmptyState";

type Assignment = {
  id: string;
  title: string;
  question: string;
  question_analysis: {
    command_words?: string[];
    topic?: string;
    scope?: string;
    required?: string[];
    interpretation?: string;
  };
  academic_level: string;
  citation_style: string;
  latest_report_id?: string | null;
  latest_score?: number | null;
  versions: { id: string; name: string; version_number: number }[];
  notes: string;
};

export default function AssignmentWorkspace() {
  const params = useParams<{ id: string }>();
  const [data, setData] = useState<Assignment | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    setError("");
    api<Assignment>(`/api/assignments/${params.id}`)
      .then(setData)
      .catch((e) => {
        setData(null);
        setError(e instanceof Error ? e.message : "Could not load this assignment.");
      })
      .finally(() => setLoading(false));
  }, [params.id]);

  if (loading) {
    return (
      <main aria-busy="true">
        <h1 className="font-serif text-3xl">Assignment workspace</h1>
        <div className="mt-8">
          <SkeletonBlock lines={6} />
        </div>
      </main>
    );
  }

  if (error || !data) {
    return (
      <main>
        <h1 className="font-serif text-3xl">Assignment workspace</h1>
        <EmptyState
          className="mt-8"
          title="Assignment unavailable"
          body={error || "This assignment could not be found, or your session expired."}
          actionHref="/app/assignments"
          actionLabel="Back to Academic Progress"
        />
        <p className="mt-4 text-sm">
          <Link href="/login" className="text-[var(--teal)] underline">
            Sign in
          </Link>
        </p>
      </main>
    );
  }

  const q = data.question_analysis || {};
  return (
    <main className="space-y-8">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="text-sm font-medium tracking-wide text-[var(--teal)]">Assignment workspace</p>
          <h1 className="mt-2 font-serif text-3xl md:text-4xl">{data.title}</h1>
          <p className="mt-2 text-sm text-[var(--ink-muted)]">
            {data.academic_level} · {data.citation_style}
            {data.latest_score != null ? ` · latest ${data.latest_score}/100` : ""}
          </p>
        </div>
        <ButtonLink href={`/app/assignments/${data.id}/check`} variant="primary">
          Check this draft
        </ButtonLink>
      </div>

      <section className="ac-surface p-5 md:p-6">
        <h2 className="font-serif text-xl">Question</h2>
        <p className="mt-3 whitespace-pre-wrap leading-7 text-[var(--ink)]">{data.question || "No question saved yet."}</p>
        {q.interpretation ? (
          <div className="mt-5 grid gap-2 border-t border-[var(--rule)] pt-5 text-sm leading-6 text-[var(--ink-muted)]">
            <p>
              <strong className="text-[var(--ink)]">Command:</strong> {(q.command_words || []).join(", ") || "—"}
            </p>
            <p>
              <strong className="text-[var(--ink)]">Topic:</strong> {q.topic || "—"}
            </p>
            <p>
              <strong className="text-[var(--ink)]">Scope:</strong> {q.scope || "—"}
            </p>
            <p>
              <strong className="text-[var(--ink)]">Required:</strong> {(q.required || []).join(", ") || "—"}
            </p>
            <p className="mt-1 text-[var(--ink)]">{q.interpretation}</p>
          </div>
        ) : null}
      </section>

      <section className="grid gap-3 sm:grid-cols-2">
        {data.latest_report_id ? (
          <Link
            className="ac-surface ac-hit justify-start p-4 text-left hover:border-[var(--teal)]/40"
            href={`/app/assignments/${data.id}/report?report=${data.latest_report_id}`}
          >
            <p className="font-medium">Latest report</p>
            <p className="mt-1 text-sm text-[var(--ink-muted)]">
              {data.latest_score != null ? `${data.latest_score}/100 · ` : ""}Open performance overview
            </p>
          </Link>
        ) : (
          <div className="ac-surface p-4">
            <p className="font-medium">No report yet</p>
            <p className="mt-1 text-sm text-[var(--ink-muted)]">Run a check to unlock your Academic Performance Overview.</p>
          </div>
        )}
        <Link className="ac-surface ac-hit justify-start p-4 text-left hover:border-[var(--teal)]/40" href={`/app/assignments/${data.id}/versions`}>
          <p className="font-medium">Versions</p>
          <p className="mt-1 text-sm text-[var(--ink-muted)]">{data.versions?.length || 0} saved draft versions</p>
        </Link>
        <Link className="ac-surface ac-hit justify-start p-4 text-left hover:border-[var(--teal)]/40" href={`/app/assignments/${data.id}/citations`}>
          <p className="font-medium">Citations</p>
          <p className="mt-1 text-sm text-[var(--ink-muted)]">Reference guidance lives on the report</p>
        </Link>
        <Link
          className="ac-surface ac-hit justify-start p-4 text-left hover:border-[var(--teal)]/40"
          href={`/app/coach?assignment=${data.id}`}
        >
          <p className="font-medium">Academic Coach</p>
          <p className="mt-1 text-sm text-[var(--ink-muted)]">Ask about thesis, paragraphs, or the question</p>
        </Link>
      </section>
    </main>
  );
}
