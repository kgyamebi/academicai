"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { SiteHeader } from "@/components/SiteHeader";
import { api, ensureGuest, track } from "@/lib/api";

const LEVELS = [
  ["high_school", "High school"],
  ["undergraduate", "Undergraduate"],
  ["masters", "Master’s"],
  ["phd", "PhD"],
  ["researcher", "Researcher"],
];

const STYLES = [
  ["apa7", "APA 7"],
  ["mla9", "MLA 9"],
  ["harvard", "Harvard"],
  ["chicago", "Chicago"],
  ["ieee", "IEEE"],
];

type Job = { id: string; status: string; stage: string; report_id?: string | null; error?: string | null };

export default function CheckPage() {
  const [question, setQuestion] = useState("Compare and evaluate the effects of globalization on developing economies.");
  const [text, setText] = useState("");
  const [level, setLevel] = useState("undergraduate");
  const [style, setStyle] = useState("apa7");
  const [file, setFile] = useState<File | NoneFile>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [job, setJob] = useState<Job | null>(null);
  const [assignmentId, setAssignmentId] = useState<string | null>(null);

  useEffect(() => {
    track("landing_page_view", "/check");
  }, []);

  async function start() {
    setError("");
    setBusy(true);
    try {
      await ensureGuest();
      track("guest_check_started", "/check");
      const assignment = await api<{ id: string }>("/api/assignments", {
        method: "POST",
        body: JSON.stringify({
          title: "Guest assignment",
          question,
          academic_level: level,
          citation_style: style,
        }),
      });
      setAssignmentId(assignment.id);
      let documentId = "";
      if (file) {
        track("document_uploaded", "/check");
        const form = new FormData();
        form.append("file", file);
        form.append("assignment_id", assignment.id);
        const doc = await api<{ id: string }>("/api/documents/upload", { method: "POST", body: form });
        documentId = doc.id;
      } else if (text.trim().length >= 40) {
        const doc = await api<{ id: string }>("/api/documents/paste", {
          method: "POST",
          body: JSON.stringify({ assignment_id: assignment.id, text, filename: "draft.txt" }),
        });
        documentId = doc.id;
      } else {
        throw new Error("Paste at least a short draft or upload a DOCX/PDF.");
      }
      track("analysis_started", "/check");
      const created = await api<Job>("/api/analysis", {
        method: "POST",
        body: JSON.stringify({ assignment_id: assignment.id, document_id: documentId, analysis_type: "full" }),
      });
      setJob(created);
      poll(created.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "We couldn’t start the check.");
      setBusy(false);
    }
  }

  async function poll(id: string) {
    const started = Date.now();
    while (Date.now() - started < 120000) {
      const current = await api<Job>(`/api/analysis/${id}`);
      setJob(current);
      if (current.status === "completed" && current.report_id) {
        track("analysis_completed", "/check");
        window.location.href = `/app/assignments/${assignmentId}/report?report=${current.report_id}`;
        return;
      }
      if (current.status === "failed" || current.status === "cancelled") {
        setError(current.error || "We couldn’t analyze this document. Please try again or upload a different file.");
        setBusy(false);
        return;
      }
      await new Promise((r) => setTimeout(r, 1200));
    }
    setError("Analysis is taking longer than expected. Open your dashboard to check the report shortly.");
    setBusy(false);
  }

  return (
    <>
      <SiteHeader />
      <main className="mx-auto max-w-3xl px-4 py-10">
        <h1 className="font-serif text-4xl">Check your assignment</h1>
        <p className="mt-3 text-[var(--ink-muted)]">
          No account required for a first look. Create a free account later to save the full report.
        </p>
        <form
          className="mt-8 space-y-5"
          onSubmit={(e) => {
            e.preventDefault();
            start();
          }}
        >
          <label className="block">
            <span className="text-sm font-medium">Assignment question</span>
            <textarea
              className="mt-2 w-full rounded-md border border-[var(--rule)] bg-white p-3"
              rows={4}
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              required
            />
          </label>
          <div className="grid gap-4 sm:grid-cols-2">
            <label className="block">
              <span className="text-sm font-medium">Academic level</span>
              <select className="mt-2 w-full rounded-md border border-[var(--rule)] bg-white p-3" value={level} onChange={(e) => setLevel(e.target.value)}>
                {LEVELS.map(([v, l]) => (
                  <option key={v} value={v}>{l}</option>
                ))}
              </select>
            </label>
            <label className="block">
              <span className="text-sm font-medium">Citation style</span>
              <select className="mt-2 w-full rounded-md border border-[var(--rule)] bg-white p-3" value={style} onChange={(e) => setStyle(e.target.value)}>
                {STYLES.map(([v, l]) => (
                  <option key={v} value={v}>{l}</option>
                ))}
              </select>
            </label>
          </div>
          <label className="block">
            <span className="text-sm font-medium">Paste your draft</span>
            <textarea
              className="mt-2 w-full rounded-md border border-[var(--rule)] bg-white p-3"
              rows={10}
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder="Paste the assignment here…"
            />
          </label>
          <label className="block">
            <span className="text-sm font-medium">Or upload DOCX / PDF / TXT</span>
            <input
              type="file"
              accept=".docx,.pdf,.txt,.md"
              className="mt-2 block w-full text-sm"
              onChange={(e) => setFile(e.target.files?.[0] || null)}
            />
          </label>
          {job && (
            <p className="rounded-md border border-[var(--rule)] bg-[var(--paper-2)] p-3 text-sm" aria-live="polite">
              Status: {job.stage.replaceAll("_", " ")} ({job.status})
            </p>
          )}
          {error && (
            <p className="rounded-md border border-[var(--crimson)] bg-red-50 p-3 text-sm" role="alert">
              {error}
            </p>
          )}
          <button type="submit" disabled={busy} className="w-full rounded-md bg-[var(--teal)] py-3 text-white disabled:opacity-60">
            {busy ? "Analyzing…" : "Start analysis"}
          </button>
        </form>
        <p className="mt-6 text-sm text-[var(--ink-muted)]">
          Already have an account? <Link href="/login" className="underline">Sign in</Link> to keep your workspace.
        </p>
      </main>
    </>
  );
}

type NoneFile = File | null;
