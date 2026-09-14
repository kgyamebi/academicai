"use client";

import { FormEvent, Suspense, useEffect, useMemo, useRef, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { api, track } from "@/lib/api";
import { Button } from "@/components/ui/Button";
import { FieldHint, FieldLabel, SelectField, TextArea } from "@/components/ui/Field";
import { EmptyState, Skeleton } from "@/components/ui/EmptyState";

type Msg = { id: string; role: "user" | "coach"; text: string; structured?: CoachParts | null };
type Assignment = {
  id: string;
  title: string;
  academic_level?: string;
  citation_style?: string;
  weakest_area?: string | null;
  latest_score?: number | null;
};

type CoachParts = { teaching?: string; reasoning?: string; example?: string; next?: string; rest?: string };

const SUGGESTED_ACTIONS = [
  { label: "Fix my citations", q: "What citation and reference issues should I fix first for this style?" },
  { label: "Improve conclusion", q: "How can I improve my conclusion so it answers the question and closes the argument?" },
  { label: "Explain this issue", q: "Explain my weakest area in plain language and what to change first." },
  { label: "Show examples", q: "Show a before-and-after example for my weakest paragraph or claim." },
  { label: "Improve academic tone", q: "Where does my tone sound informal, and how should I revise those sentences?" },
  { label: "Generate a stronger argument", q: "Help me strengthen the main argument so each paragraph advances a contestable claim." },
];

function structureCoach(text: string): CoachParts {
  const parts: CoachParts = {};
  const cleaned = text.trim();
  const nextMatch = cleaned.match(/(?:next step|try this|action)[:\s—-]+([\s\S]+)/i);
  const exampleMatch = cleaned.match(/(?:example|for instance)[:\s—-]+([\s\S]+?)(?=(?:next step|try this|action|$))/i);
  if (exampleMatch) parts.example = exampleMatch[1].trim().slice(0, 600);
  if (nextMatch) parts.next = nextMatch[1].trim().slice(0, 400);
  const paras = cleaned.split(/\n\n+/).filter(Boolean);
  if (paras[0]) parts.teaching = paras[0].slice(0, 500);
  if (paras[1] && !parts.reasoning) parts.reasoning = paras[1].slice(0, 500);
  if (!parts.teaching) parts.rest = cleaned;
  return parts;
}

export default function CoachPage() {
  return (
    <Suspense
      fallback={
        <main className="mx-auto max-w-3xl px-4 py-10">
          <h1 className="font-serif text-3xl">Writing coach</h1>
          <Skeleton className="mt-8 h-40 w-full rounded-[var(--radius-md)]" />
        </main>
      }
    >
      <CoachPageInner />
    </Suspense>
  );
}

function CoachPageInner() {
  const search = useSearchParams();
  const [assignments, setAssignments] = useState<Assignment[] | null>(null);
  const [assignmentId, setAssignmentId] = useState("");
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState<Msg[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const presetQ = search.get("q");
    if (presetQ) setQuestion(presetQ);
  }, [search]);

  useEffect(() => {
    api<{ items: Assignment[] }>("/api/assignments")
      .then((d) => {
        const items = d.items || [];
        setAssignments(items);
        const fromQuery = search.get("assignment");
        if (fromQuery && items.some((a) => a.id === fromQuery)) {
          setAssignmentId(fromQuery);
        } else if (items[0]) {
          setAssignmentId(items[0].id);
        }
      })
      .catch(() => setAssignments([]));
  }, [search]);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages, busy]);

  const current = useMemo(() => assignments?.find((a) => a.id === assignmentId), [assignments, assignmentId]);

  async function ask(prompt: string) {
    if (!assignmentId || !prompt.trim()) return;
    setError("");
    setBusy(true);
    const userMsg: Msg = { id: `u-${Date.now()}`, role: "user", text: prompt.trim() };
    setMessages((m) => [...m, userMsg]);
    setQuestion("");
    try {
      const data = await api<{ answer: string; disclaimer: string }>("/api/coach", {
        method: "POST",
        body: JSON.stringify({ assignment_id: assignmentId, question: prompt.trim() }),
      });
      const structured = structureCoach(data.answer);
      setMessages((m) => [
        ...m,
        {
          id: `c-${Date.now()}`,
          role: "coach",
          text: `${data.answer}\n\n${data.disclaimer}`,
          structured,
        },
      ]);
      track("coach_used", "/app/coach");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Your mentor is unavailable right now.");
      setMessages((m) => m.filter((x) => x.id !== userMsg.id));
      setQuestion(prompt);
    } finally {
      setBusy(false);
    }
  }

  async function onSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    await ask(question);
  }

  if (assignments === null) {
    return (
      <main className="mx-auto max-w-2xl" aria-busy="true">
        <p className="text-sm font-medium tracking-wide text-[var(--teal)]">Academic Mentor</p>
        <h1 className="mt-2 font-serif text-3xl">Academic Mentor</h1>
        <div className="mt-8 space-y-3">
          <Skeleton className="h-24 w-full rounded-[var(--radius-md)]" />
          <Skeleton className="h-12 w-full rounded-[var(--radius-md)]" />
          <Skeleton className="h-40 w-full rounded-[var(--radius-md)]" />
        </div>
      </main>
    );
  }

  if (!assignments.length) {
    return (
      <main className="mx-auto max-w-2xl">
        <p className="text-sm font-medium tracking-wide text-[var(--teal)]">Academic Mentor</p>
        <h1 className="mt-2 font-serif text-3xl md:text-4xl">Guidance tied to your draft</h1>
        <EmptyState
          className="mt-8"
          kicker="Academic Mentor"
          title="Your mentor needs an assignment"
          body="Upload your first essay. The mentor uses your report context — strengths, weaknesses, and citation style — so advice never feels generic."
          actionHref="/check"
          actionLabel="Analyze Essay"
        />
      </main>
    );
  }

  return (
    <main className="mx-auto flex min-h-[70vh] max-w-2xl flex-col">
      <div>
        <p className="text-sm font-medium tracking-wide text-[var(--teal)]">Academic Mentor</p>
        <h1 className="mt-2 font-serif text-3xl md:text-4xl">Ask with purpose</h1>
        <p className="mt-3 text-sm leading-7 text-[var(--ink-muted)]">
          Advisor-style guidance on <em>your</em> work — not a chatbot that invents sources or writes the paper.
        </p>
      </div>

      <section className="ac-surface mt-6 p-4 md:p-5" aria-label="Report context">
        <p className="text-xs font-semibold uppercase tracking-wide text-[var(--ink-muted)]">Working from</p>
        <div className="mt-3 grid gap-3 sm:grid-cols-2">
          <div className="sm:col-span-2">
            <FieldLabel htmlFor="assignment_id">Assignment</FieldLabel>
            <SelectField
              id="assignment_id"
              value={assignmentId}
              onChange={(e) => setAssignmentId(e.target.value)}
              disabled={busy}
            >
              {assignments.map((a) => (
                <option key={a.id} value={a.id}>
                  {a.title}
                </option>
              ))}
            </SelectField>
          </div>
          <p className="text-sm">
            <span className="text-[var(--ink-muted)]">Level · </span>
            {(current?.academic_level || "—").replaceAll("_", " ")}
          </p>
          <p className="text-sm">
            <span className="text-[var(--ink-muted)]">Citations · </span>
            {(current?.citation_style || "—").toUpperCase()}
          </p>
          <p className="text-sm sm:col-span-2">
            <span className="text-[var(--ink-muted)]">Focus · </span>
            {current?.weakest_area || "Run an analysis to identify your weakest area"}
            {current?.latest_score != null ? ` · latest ${current.latest_score}/100` : ""}
          </p>
        </div>
      </section>

      <div className="mt-5">
        <p className="text-xs font-semibold uppercase tracking-wide text-[var(--ink-muted)]">Suggested actions</p>
        <div className="mt-2 flex flex-wrap gap-2" role="group" aria-label="Suggested actions">
          {SUGGESTED_ACTIONS.map((s) => (
            <button
              key={s.label}
              type="button"
              disabled={busy}
              onClick={() => ask(s.q)}
              className="ac-hit ac-press rounded-full border border-[var(--rule)] bg-[var(--paper-2)] px-3 text-sm transition-colors hover:border-[var(--teal)]/40 hover:text-[var(--teal)]"
            >
              {s.label}
            </button>
          ))}
        </div>
      </div>

      <div className="mt-6 flex-1 space-y-4" aria-live="polite">
        {messages.length === 0 ? (
          <div className="ac-surface p-5 md:p-6">
            <p className="font-serif text-xl">Start with what matters most</p>
            <p className="mt-2 text-sm leading-7 text-[var(--ink-muted)]">
              Pick a suggested action, or ask one specific question about this assignment. Narrow coaching beats
              generic chat.
            </p>
          </div>
        ) : (
          messages.map((m) =>
            m.role === "user" ? (
              <div
                key={m.id}
                className="ac-reveal ml-auto max-w-[92%] rounded-[var(--radius-md)] bg-[var(--teal)] px-4 py-3 text-sm leading-7 text-white"
              >
                <p className="mb-1 text-[10px] font-semibold uppercase tracking-wide text-white/80">You</p>
                <p className="whitespace-pre-wrap">{m.text}</p>
              </div>
            ) : (
              <article
                key={m.id}
                className="ac-reveal mr-auto max-w-[95%] space-y-3 rounded-[var(--radius-md)] border border-[var(--rule)] bg-[var(--paper-2)] p-4 text-sm leading-7 md:p-5"
              >
                <p className="text-[10px] font-semibold uppercase tracking-wide text-[var(--teal)]">Academic Mentor</p>
                {m.structured?.teaching || m.structured?.reasoning || m.structured?.example || m.structured?.next ? (
                  <>
                    {m.structured.teaching ? (
                      <div>
                        <p className="text-xs font-semibold uppercase tracking-wide text-[var(--ink-muted)]">Guidance</p>
                        <p className="mt-1 font-serif text-base leading-7">{m.structured.teaching}</p>
                      </div>
                    ) : null}
                    {m.structured.reasoning ? (
                      <div>
                        <p className="text-xs font-semibold uppercase tracking-wide text-[var(--ink-muted)]">Why it matters</p>
                        <p className="mt-1">{m.structured.reasoning}</p>
                      </div>
                    ) : null}
                    {m.structured.example ? (
                      <div>
                        <p className="text-xs font-semibold uppercase tracking-wide text-[var(--ink-muted)]">Example</p>
                        <p className="mt-1 italic text-[var(--ink-muted)]">{m.structured.example}</p>
                      </div>
                    ) : null}
                    {m.structured.next ? (
                      <div className="rounded-[var(--radius-sm)] bg-[var(--teal-soft)]/50 px-3 py-2">
                        <p className="text-xs font-semibold uppercase tracking-wide text-[var(--teal)]">Next step</p>
                        <p className="mt-1 font-medium">{m.structured.next}</p>
                      </div>
                    ) : null}
                    <details className="text-xs text-[var(--ink-muted)]">
                      <summary className="cursor-pointer">Full response</summary>
                      <p className="mt-2 whitespace-pre-wrap leading-6">{m.text}</p>
                    </details>
                  </>
                ) : (
                  <p className="whitespace-pre-wrap font-serif text-base leading-7">{m.text}</p>
                )}
              </article>
            ),
          )
        )}
        {busy ? (
          <div className="ac-surface space-y-2 p-4" aria-busy="true">
            <Skeleton className="h-3 w-1/3" />
            <Skeleton className="h-3 w-full" />
            <Skeleton className="h-3 w-5/6" />
            <span className="sr-only">Mentor is preparing guidance…</span>
          </div>
        ) : null}
        <div ref={endRef} />
      </div>

      {error ? (
        <p role="alert" className="mt-4 text-sm text-[var(--crimson)]">
          {error}
        </p>
      ) : null}

      <form
        onSubmit={onSubmit}
        className="sticky bottom-20 z-10 mt-6 space-y-3 border-t border-[var(--rule)] bg-[var(--paper)]/95 pt-4 backdrop-blur md:bottom-0"
      >
        <FieldLabel htmlFor="question">Your question</FieldLabel>
        <TextArea
          id="question"
          name="question"
          required
          rows={3}
          value={question}
          disabled={busy}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="How do I turn my topic sentence into a contestable thesis?"
          aria-describedby="coach-hint"
        />
        <FieldHint id="coach-hint">Keep questions specific to this assignment and report.</FieldHint>
        <div className="flex flex-wrap items-center gap-3">
          <Button type="submit" busy={busy} variant="primary">
            Ask mentor
          </Button>
          <Link href="/app/assignments" className="text-sm text-[var(--ink-muted)] underline-offset-4 hover:underline">
            Academic Progress
          </Link>
        </div>
      </form>
    </main>
  );
}
