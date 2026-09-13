"use client";

import { FormEvent, useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { api } from "@/lib/api";
import { ScoreRing } from "@/components/ScoreRing";
import { Button } from "@/components/ui/Button";
import { FieldError, FieldLabel, TextField } from "@/components/ui/Field";
import { SkeletonBlock } from "@/components/ui/EmptyState";

type Shared = {
  overall_score: number;
  summary: string;
  disclaimer: string;
  strengths?: string[];
  weaknesses?: string[];
  priority_actions?: string[];
  scores?: { category: string; score: number; rationale?: string }[];
};

export default function SharedReport() {
  const params = useParams<{ token: string }>();
  const [report, setReport] = useState<Shared | null>(null);
  const [error, setError] = useState("");
  const [needsPassword, setNeedsPassword] = useState(false);

  useEffect(() => {
    api<Shared>(`/api/reports/shared/${params.token}`)
      .then(setReport)
      .catch((err: Error) => {
        if (/password/i.test(err.message)) setNeedsPassword(true);
        else setError("This share link is unavailable.");
      });
  }, [params.token]);

  async function unlock(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = new FormData(e.currentTarget);
    try {
      const data = await api<Shared>(`/api/reports/shared/${params.token}`, {
        method: "POST",
        body: JSON.stringify({ password: form.get("password") }),
      });
      setReport(data);
      setNeedsPassword(false);
      setError("");
    } catch {
      setError("Incorrect share password.");
    }
  }

  if (needsPassword && !report) {
    return (
      <main id="main-content" tabIndex={-1} className="mx-auto max-w-md px-4 py-16">
        <p className="text-sm font-medium tracking-wide text-[var(--teal)]">Shared report</p>
        <h1 className="mt-2 font-serif text-3xl">Protected analysis</h1>
        <p className="mt-3 text-sm text-[var(--ink-muted)]">Enter the share password to view this diagnostic report.</p>
        <form onSubmit={unlock} className="mt-8 space-y-4">
          <div>
            <FieldLabel htmlFor="share-password">Password</FieldLabel>
            <TextField
              id="share-password"
              name="password"
              type="password"
              required
              aria-invalid={Boolean(error)}
              aria-describedby={error ? "share-error" : undefined}
            />
          </div>
          {error ? <FieldError id="share-error">{error}</FieldError> : null}
          <Button type="submit" variant="primary" className="w-full">
            Open report
          </Button>
        </form>
      </main>
    );
  }

  if (error) {
    return (
      <main id="main-content" tabIndex={-1} className="mx-auto max-w-lg px-4 py-16">
        <h1 className="font-serif text-3xl">Unavailable</h1>
        <p role="alert" className="mt-4 text-[var(--ink-muted)]">
          {error}
        </p>
        <Link href="/" className="mt-6 inline-block text-[var(--teal)] underline">
          Go to AcademicCheck AI
        </Link>
      </main>
    );
  }

  if (!report) {
    return (
      <main id="main-content" tabIndex={-1} className="mx-auto max-w-2xl px-4 py-16">
        <h1 className="font-serif text-3xl">Shared analysis</h1>
        <div className="mt-8">
          <SkeletonBlock lines={6} />
        </div>
      </main>
    );
  }

  return (
    <main id="main-content" tabIndex={-1} className="min-h-screen bg-[var(--paper)]">
      <div className="border-b border-[var(--rule)] bg-[var(--paper-2)]">
        <div className="mx-auto flex max-w-3xl items-center justify-between gap-4 px-4 py-4">
          <Link href="/" className="font-serif text-lg">
            AcademicCheck <span className="text-[var(--teal)]">AI</span>
          </Link>
          <p className="text-xs text-[var(--ink-muted)]">Shared diagnostic report</p>
        </div>
      </div>

      <article className="mx-auto max-w-3xl px-4 py-12 md:py-16">
        <p className="text-sm font-medium tracking-wide text-[var(--teal)]">Academic performance</p>
        <h1 className="mt-2 font-serif text-4xl md:text-5xl">Shared analysis</h1>
        <p className="mt-3 max-w-2xl text-sm leading-7 text-[var(--ink-muted)]">
          Prepared for tutors, lecturers, or peers. This is an AI-assisted diagnostic — not an official grade.
        </p>

        <div className="ac-surface mt-10 p-6 md:p-8">
          <ScoreRing score={report.overall_score} label="Overall diagnostic score" />
          <p className="mt-6 text-base leading-8 text-[var(--ink)]">{report.summary}</p>
        </div>

        {report.scores?.length ? (
          <section className="mt-10">
            <h2 className="font-serif text-2xl">Dimensions</h2>
            <ul className="mt-4 divide-y divide-[var(--rule)] overflow-hidden rounded-[var(--radius-md)] border border-[var(--rule)] bg-[var(--paper-2)]">
              {report.scores.map((s) => (
                <li key={s.category} className="flex items-baseline justify-between gap-4 px-4 py-3 text-sm">
                  <span className="capitalize text-[var(--ink)]">{s.category.replaceAll("_", " ")}</span>
                  <span className="font-serif text-xl tabular-nums">{s.score}</span>
                </li>
              ))}
            </ul>
          </section>
        ) : null}

        {(report.priority_actions?.length || report.strengths?.length || report.weaknesses?.length) && (
          <section className="mt-10 grid gap-5 md:grid-cols-2">
            {report.priority_actions?.length ? (
              <div className="ac-surface p-5">
                <h2 className="font-serif text-xl">Priority fixes</h2>
                <ol className="mt-3 list-decimal space-y-2 pl-5 text-sm leading-7">
                  {report.priority_actions.slice(0, 5).map((a) => (
                    <li key={a}>{a}</li>
                  ))}
                </ol>
              </div>
            ) : null}
            <div className="space-y-5">
              {report.strengths?.length ? (
                <div className="ac-surface p-5">
                  <h2 className="font-serif text-xl">Strengths</h2>
                  <ul className="mt-3 list-disc space-y-2 pl-5 text-sm leading-7">
                    {report.strengths.map((s) => (
                      <li key={s}>{s}</li>
                    ))}
                  </ul>
                </div>
              ) : null}
              {report.weaknesses?.length ? (
                <div className="ac-surface p-5">
                  <h2 className="font-serif text-xl">Needs attention</h2>
                  <ul className="mt-3 list-disc space-y-2 pl-5 text-sm leading-7">
                    {report.weaknesses.map((s) => (
                      <li key={s}>{s}</li>
                    ))}
                  </ul>
                </div>
              ) : null}
            </div>
          </section>
        )}

        <footer className="mt-12 border-t border-[var(--rule)] pt-6">
          <p className="text-sm leading-7 text-[var(--ink-muted)]">{report.disclaimer}</p>
          <p className="mt-4 text-sm">
            <Link href="/check" className="font-medium text-[var(--teal)] underline-offset-4 hover:underline">
              Check your own assignment
            </Link>
          </p>
        </footer>
      </article>
    </main>
  );
}
