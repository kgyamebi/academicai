"use client";

import { FormEvent, useEffect, useState } from "react";
import { api, track } from "@/lib/api";

export default function CoachPage() {
  const [assignments, setAssignments] = useState<{ id: string; title: string }[]>([]);
  const [answer, setAnswer] = useState("");
  useEffect(() => {
    api<{ items: { id: string; title: string }[] }>("/api/assignments").then((d) => setAssignments(d.items));
  }, []);
  async function onSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = new FormData(e.currentTarget);
    const data = await api<{ answer: string; disclaimer: string }>("/api/coach", {
      method: "POST",
      body: JSON.stringify({ assignment_id: form.get("assignment_id"), question: form.get("question") }),
    });
    setAnswer(`${data.answer}\n\n${data.disclaimer}`);
    track("coach_used", "/app/coach");
  }
  return (
    <main className="max-w-2xl">
      <h1 className="font-serif text-3xl">Academic Coach</h1>
      <p className="mt-2 text-sm text-[var(--ink-muted)]">Ask about your thesis, a paragraph, or the question. The coach will not invent sources or write the assignment for you.</p>
      <form onSubmit={onSubmit} className="mt-6 space-y-4">
        <label className="block text-sm">Assignment
          <select name="assignment_id" required className="mt-1 w-full rounded-md border border-[var(--rule)] bg-white p-3">
            {assignments.map((a) => <option key={a.id} value={a.id}>{a.title}</option>)}
          </select>
        </label>
        <label className="block text-sm">Question
          <textarea name="question" required rows={4} className="mt-1 w-full rounded-md border border-[var(--rule)] bg-white p-3" placeholder="Why is my thesis weak?" />
        </label>
        <button type="submit" className="rounded-md bg-[var(--teal)] px-4 py-2 text-white">Ask the coach</button>
      </form>
      {answer && <p className="mt-6 whitespace-pre-wrap rounded-lg border border-[var(--rule)] bg-[var(--paper-2)] p-4 text-sm leading-7">{answer}</p>}
    </main>
  );
}
