"use client";

import { useEffect, useState } from "react";
import { animateValue, easeInOutCubic, prefersReducedMotion } from "@/lib/motion";

const OVERALL = 84;

const METRICS = [
  { label: "Question Alignment", value: 63 },
  { label: "Thesis Strength", value: 78 },
  { label: "Evidence Quality", value: 54 },
  { label: "Citation Quality", value: 91 },
] as const;

const WEAK = ["Under-addresses evaluate command", "Two claims need deeper sources", "Style drift in references"];

type Phase = "upload" | "analyzing" | "score" | "metrics" | "weak" | "hold";

/**
 * Homepage live demo — 8–10s loop with overall score + metric bars.
 */
export function HeroLiveDemo() {
  const [phase, setPhase] = useState<Phase>("upload");
  const [step, setStep] = useState(0);
  const [shownMetrics, setShownMetrics] = useState(0);
  const [overall, setOverall] = useState(0);

  useEffect(() => {
    if (prefersReducedMotion()) {
      setPhase("weak");
      setShownMetrics(METRICS.length);
      setOverall(OVERALL);
      setStep(4);
      return;
    }

    let cancelled = false;
    const timers: number[] = [];
    let stopScore: (() => void) | undefined;
    const wait = (ms: number) =>
      new Promise<void>((resolve) => {
        timers.push(window.setTimeout(resolve, ms));
      });

    async function loop() {
      while (!cancelled) {
        setPhase("upload");
        setStep(0);
        setShownMetrics(0);
        setOverall(0);
        await wait(800);

        setPhase("analyzing");
        for (let i = 0; i < 4; i += 1) {
          if (cancelled) return;
          setStep(i);
          await wait(650);
        }

        setPhase("score");
        stopScore = animateValue({
          from: 0,
          to: OVERALL,
          duration: 1100,
          ease: easeInOutCubic,
          onUpdate: (v) => setOverall(Math.round(v)),
        });
        await wait(1300);

        setPhase("metrics");
        for (let i = 1; i <= METRICS.length; i += 1) {
          if (cancelled) return;
          setShownMetrics(i);
          await wait(480);
        }

        setPhase("weak");
        await wait(1500);

        setPhase("hold");
        await wait(800);
      }
    }

    void loop();
    return () => {
      cancelled = true;
      stopScore?.();
      timers.forEach((id) => window.clearTimeout(id));
    };
  }, []);

  const scanLabels = [
    "Analyzing Assignment Brief…",
    "Evaluating Thesis…",
    "Reviewing Evidence…",
    "Checking Citations…",
  ];

  return (
    <div
      className="relative overflow-hidden rounded-[var(--radius-lg)] border border-[var(--rule)] bg-[var(--paper-2)] shadow-[var(--shadow-1)]"
      aria-label="Live demonstration of an AcademicCheck diagnostic report"
    >
      <div className="border-b border-[var(--rule)] bg-[var(--paper)] px-5 py-3">
        <p className="text-xs font-semibold uppercase tracking-wide text-[var(--teal)]">Live diagnostic</p>
        <p className="mt-1 text-sm text-[var(--ink-muted)]">
          {phase === "upload"
            ? "Student uploads paper…"
            : phase === "analyzing"
              ? "Running academic health scan…"
              : phase === "score"
                ? "Overall score landing…"
                : "Report assembling"}
        </p>
      </div>

      <div className="relative min-h-[300px] p-5">
        {(phase === "analyzing" || phase === "upload") && (
          <div className="space-y-3">
            {phase === "upload" ? (
              <p className="ac-settle text-sm text-[var(--ink-muted)]">essay_draft.docx · 2,400 words</p>
            ) : null}
            {scanLabels.map((label, i) => {
              const done = step > i;
              const active = step === i && phase === "analyzing";
              if (phase === "upload" && i > 0) return null;
              return (
                <div
                  key={label}
                  className={`flex items-center gap-3 text-sm ${done || active ? "ac-step-enter" : "opacity-40"}`}
                >
                  <span
                    className={`grid h-5 w-5 place-items-center rounded-full text-[10px] ${
                      done
                        ? "bg-[var(--forest)] text-white"
                        : active
                          ? "border border-[var(--teal)] text-[var(--teal)]"
                          : "border border-[var(--rule)]"
                    }`}
                  >
                    {done ? "✓" : ""}
                  </span>
                  <span className={active ? "font-medium text-[var(--ink)]" : "text-[var(--ink)]"}>{label}</span>
                </div>
              );
            })}
          </div>
        )}

        {(phase === "score" || phase === "metrics" || phase === "weak" || phase === "hold") && (
          <div className="space-y-5">
            <div className="ac-settle flex items-end gap-3">
              <p className="font-serif text-5xl tabular-nums tracking-tight text-[var(--ink)]">{overall}</p>
              <div className="pb-1">
                <p className="text-sm font-medium text-[var(--ink)]">Overall Score</p>
                <p className="text-xs text-[var(--teal)]">Academic Health · Strong Draft</p>
              </div>
            </div>

            {(phase === "metrics" || phase === "weak" || phase === "hold") && (
              <ul className="space-y-3">
                {METRICS.slice(0, shownMetrics).map((m) => (
                  <li key={m.label} className="ac-settle">
                    <div className="mb-1 flex items-center justify-between gap-3 text-sm">
                      <span className="text-[var(--ink)]">{m.label}</span>
                      <span className="font-serif tabular-nums text-[var(--teal)]">{m.value}%</span>
                    </div>
                    <div className="h-1 overflow-hidden rounded-full bg-[var(--rule)]">
                      <div
                        className="ac-metric-bar h-full rounded-full bg-[var(--teal)]"
                        style={{ width: `${m.value}%` }}
                      />
                    </div>
                  </li>
                ))}
              </ul>
            )}

            {(phase === "weak" || phase === "hold") && (
              <div className="ac-settle border-t border-[var(--rule)] pt-4">
                <p className="text-xs font-semibold uppercase tracking-wide text-[var(--ink-muted)]">Weak areas found</p>
                <ul className="mt-2 space-y-1.5 text-sm text-[var(--ink)]">
                  {WEAK.map((w) => (
                    <li key={w}>· {w}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
