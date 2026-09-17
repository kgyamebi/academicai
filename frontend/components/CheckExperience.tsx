"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { AnalysisRitual, type UploadPhase } from "@/components/AnalysisRitual";
import { useAuth } from "@/components/AuthProvider";
import { SiteHeader } from "@/components/SiteHeader";
import { Button } from "@/components/ui/Button";
import { Dropzone } from "@/components/ui/Dropzone";
import { FieldError, FieldHint, FieldLabel, SelectField, TextArea } from "@/components/ui/Field";
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

export function CheckExperience({ embedded = false }: { embedded?: boolean }) {
  const { user, signedIn, needsVerify } = useAuth();
  const [question, setQuestion] = useState("");
  const [text, setText] = useState("");
  const [level, setLevel] = useState("undergraduate");
  const [style, setStyle] = useState("apa7");
  const [file, setFile] = useState<File | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [job, setJob] = useState<Job | null>(null);
  const [assignmentId, setAssignmentId] = useState<string | null>(null);
  const [phase, setPhase] = useState<UploadPhase>("idle");

  useEffect(() => {
    track("landing_page_view", "/check");
    try {
      const raw = sessionStorage.getItem("ac_onboarding");
      if (!raw) return;
      const prefs = JSON.parse(raw) as { level?: string; style?: string };
      if (prefs.level) setLevel(prefs.level);
      if (prefs.style) setStyle(prefs.style);
    } catch {
      /* ignore */
    }
  }, []);

  const wordCount = text.trim() ? text.trim().split(/\s+/).length : 0;

  function resetFlow() {
    setBusy(false);
    setJob(null);
    setPhase("idle");
    setError("");
  }

  async function start() {
    setError("");
    setBusy(true);
    setPhase(file ? "uploading" : "processing");
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
        setPhase("uploading");
        const form = new FormData();
        form.append("file", file);
        form.append("assignment_id", assignment.id);
        const uploaded = await api<{ id: string; status: string; extraction_error?: string | null }>(
          "/api/documents/upload",
          { method: "POST", body: form },
        );
        documentId = uploaded.id;
        setPhase("processing");
        const startedWait = Date.now();
        let current = uploaded;
        while (current.status === "queued" || current.status === "extracting") {
          if (Date.now() - startedWait > 120000) {
            throw new Error("Document processing is taking longer than expected. Try a smaller file.");
          }
          await new Promise((r) => setTimeout(r, 400));
          current = await api<{ id: string; status: string; extraction_error?: string | null }>(
            `/api/documents/${documentId}`,
          );
        }
        if (current.status !== "extracted") {
          throw new Error(current.extraction_error || "We could not read this document. Try a PDF, DOCX, or TXT file.");
        }
      } else if (text.trim().length >= 40) {
        setPhase("processing");
        const doc = await api<{ id: string }>("/api/documents/paste", {
          method: "POST",
          body: JSON.stringify({ assignment_id: assignment.id, text, filename: "draft.txt" }),
        });
        documentId = doc.id;
      } else {
        throw new Error("Paste at least a short draft or upload a DOCX/PDF.");
      }
      track("analysis_started", "/check");
      setPhase("analyzing");
      const created = await api<Job>("/api/analysis", {
        method: "POST",
        body: JSON.stringify({ assignment_id: assignment.id, document_id: documentId, analysis_type: "full" }),
      });
      setJob(created);
      poll(created.id);
    } catch (err) {
      setPhase("failed");
      setError(err instanceof Error ? err.message : "We couldn’t start the check.");
      setBusy(false);
    }
  }

  async function poll(id: string) {
    const started = Date.now();
    try {
      while (Date.now() - started < 120000) {
        const current = await api<Job>(`/api/analysis/${id}`);
        setJob(current);
        if (/report|scor|build|generat/i.test(current.stage || "")) {
          setPhase("generating");
        } else {
          setPhase("analyzing");
        }
        if (current.status === "completed" && current.report_id) {
          setPhase("completed");
          track("analysis_completed", "/check");
          window.location.href = `/app/assignments/${assignmentId}/report?report=${current.report_id}`;
          return;
        }
        if (current.status === "failed" || current.status === "cancelled") {
          setPhase("failed");
          setError(current.error || "We couldn’t analyze this document. Please try again or upload a different file.");
          setBusy(false);
          return;
        }
        await new Promise((r) => setTimeout(r, 1200));
      }
      setPhase("failed");
      setError("Analysis is taking longer than expected. Open your dashboard to check the report shortly.");
    } catch {
      setPhase("failed");
      setError("We lost the connection while analyzing. Open your dashboard to check the report, or try again.");
    }
    setBusy(false);
  }

  const showRitual = busy || phase === "failed" || phase === "completed" || Boolean(job);

  return (
    <>
      {!embedded && <SiteHeader />}
      <main
        id={embedded ? undefined : "main-content"}
        tabIndex={embedded ? undefined : -1}
        className="mx-auto max-w-3xl px-4 py-12 md:py-16"
      >
        <p className="ac-enter text-sm font-medium tracking-wide text-[var(--teal)]">Free public check</p>
        <h1 className="ac-enter ac-enter-delay-1 mt-3 font-serif text-4xl md:text-5xl">Check your assignment</h1>
        <p className="ac-enter ac-enter-delay-2 mt-4 max-w-2xl text-[var(--ink-muted)] leading-7">
          No account required for a first look. Create a free account later to save the full report and keep improving.
        </p>

        <form
          className="ac-enter ac-enter-delay-3 mt-10 space-y-7"
          onSubmit={(e) => {
            e.preventDefault();
            start();
          }}
        >
          <div>
            <FieldLabel htmlFor="question">Assignment question</FieldLabel>
            <TextArea
              id="question"
              name="question"
              rows={4}
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              required
              disabled={busy}
              aria-invalid={Boolean(error)}
              placeholder="e.g. Critically evaluate… / Compare and contrast…"
              aria-describedby={error ? "question-hint check-error" : "question-hint"}
            />
            <FieldHint id="question-hint">
              Paste the lecturer’s question. Leave blank only if your file already includes it — better to paste it here.
            </FieldHint>
          </div>

          <fieldset className="grid gap-5 sm:grid-cols-2">
            <legend className="sr-only">Academic level and citation style</legend>
            <div>
              <FieldLabel htmlFor="level">Academic level</FieldLabel>
              <SelectField
                id="level"
                name="level"
                value={level}
                disabled={busy}
                onChange={(e) => setLevel(e.target.value)}
              >
                {LEVELS.map(([v, l]) => (
                  <option key={v} value={v}>
                    {l}
                  </option>
                ))}
              </SelectField>
            </div>
            <div>
              <FieldLabel htmlFor="style">Citation style</FieldLabel>
              <SelectField
                id="style"
                name="style"
                value={style}
                disabled={busy}
                onChange={(e) => setStyle(e.target.value)}
              >
                {STYLES.map(([v, l]) => (
                  <option key={v} value={v}>
                    {l}
                  </option>
                ))}
              </SelectField>
            </div>
          </fieldset>

          <div>
            <FieldLabel htmlFor="draft" hint={wordCount ? `${wordCount} words` : undefined}>
              Paste your draft
            </FieldLabel>
            <TextArea
              id="draft"
              name="draft"
              rows={10}
              value={text}
              disabled={busy}
              onChange={(e) => setText(e.target.value)}
              placeholder="Paste the assignment here…"
              aria-describedby="draft-hint"
            />
            <FieldHint id="draft-hint">Paste at least a short draft, or upload a file below.</FieldHint>
          </div>

          <div>
            <p className="mb-2 text-sm font-medium">Or upload a file</p>
            <Dropzone file={file} onFile={setFile} disabled={busy} />
          </div>

          {showRitual ? (
            <AnalysisRitual
              phase={phase}
              stage={job?.stage}
              status={job?.status || (phase === "failed" ? "failed" : undefined)}
              onRetry={phase === "failed" ? resetFlow : undefined}
            />
          ) : null}
          {error && <FieldError id="check-error">{error}</FieldError>}
          {error && assignmentId ? (
            <p className="text-sm text-[var(--ink-muted)]">
              <Link href="/app/dashboard" className="font-medium text-[var(--teal)] underline-offset-4 hover:underline">
                Open dashboard
              </Link>{" "}
              to see if a report finished in the background.
            </p>
          ) : null}

          <Button type="submit" busy={busy} className="w-full sm:w-auto sm:min-w-[220px]" variant="primary">
            {phase === "failed" ? "Try again" : "Start analysis"}
          </Button>
        </form>

        {signedIn ? (
          <p className="mt-8 text-sm text-[var(--ink-muted)]">
            Signed in as{" "}
            <span className="font-medium text-[var(--ink)]">{user?.email || user?.full_name || "your account"}</span>
            {" · "}
            <Link href="/app/dashboard" className="font-medium text-[var(--teal)] underline-offset-4 hover:underline">
              Dashboard
            </Link>
            {needsVerify ? (
              <>
                {" · "}
                <Link href="/app/settings" className="font-medium text-[var(--amber)] underline-offset-4 hover:underline">
                  Waiting for email verification
                </Link>
              </>
            ) : null}
          </p>
        ) : (
          <p className="mt-8 text-sm text-[var(--ink-muted)]">
            Already have an account?{" "}
            <Link href="/login" className="font-medium text-[var(--teal)] underline-offset-4 hover:underline">
              Sign in
            </Link>{" "}
            to keep your workspace.
          </p>
        )}
      </main>
    </>
  );
}
