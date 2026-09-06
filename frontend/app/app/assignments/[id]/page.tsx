"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { api } from "@/lib/api";

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
  useEffect(() => {
    api<Assignment>(`/api/assignments/${params.id}`).then(setData).catch(() => setData(null));
  }, [params.id]);
  if (!data) return <p>Loading workspace…</p>;
  const q = data.question_analysis || {};
  return (
    <main className="space-y-8">
      <div>
        <p className="text-sm text-[var(--ink-muted)]">Assignment workspace</p>
        <h1 className="font-serif text-3xl">{data.title}</h1>
        <p className="text-sm">{data.academic_level} · {data.citation_style}</p>
      </div>
      <section className="rounded-xl border border-[var(--rule)] bg-[var(--paper-2)] p-5">
        <h2 className="font-serif text-xl">Question</h2>
        <p className="mt-2 whitespace-pre-wrap leading-7">{data.question}</p>
        {q.interpretation && (
          <div className="mt-4 text-sm leading-6">
            <p><strong>Command:</strong> {(q.command_words || []).join(", ") || "—"}</p>
            <p><strong>Topic:</strong> {q.topic || "—"}</p>
            <p><strong>Scope:</strong> {q.scope || "—"}</p>
            <p><strong>Required:</strong> {(q.required || []).join(", ") || "—"}</p>
            <p className="mt-2">{q.interpretation}</p>
          </div>
        )}
      </section>
      <section className="grid gap-3 sm:grid-cols-2">
        <Link className="rounded-lg border border-[var(--rule)] p-4" href={`/app/assignments/${data.id}/check`}>Check this draft</Link>
        {data.latest_report_id && (
          <Link className="rounded-lg border border-[var(--rule)] p-4" href={`/app/assignments/${data.id}/report?report=${data.latest_report_id}`}>
            Latest report {data.latest_score != null ? `(${data.latest_score}/100)` : ""}
          </Link>
        )}
        <Link className="rounded-lg border border-[var(--rule)] p-4" href={`/app/assignments/${data.id}/versions`}>Versions</Link>
        <Link className="rounded-lg border border-[var(--rule)] p-4" href={`/app/assignments/${data.id}/citations`}>Citations</Link>
        <Link className="rounded-lg border border-[var(--rule)] p-4" href="/app/coach">Academic Coach</Link>
      </section>
    </main>
  );
}
