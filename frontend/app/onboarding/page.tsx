"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { SiteHeader } from "@/components/SiteHeader";
import { Button } from "@/components/ui/Button";

const LEVELS = [
  ["high_school", "High school"],
  ["undergraduate", "Undergraduate"],
  ["masters", "Master’s"],
  ["phd", "PhD"],
  ["researcher", "Researcher"],
];

const AREAS = [
  "Social sciences",
  "Humanities",
  "Business & economics",
  "STEM",
  "Law",
  "Health & medicine",
  "Education",
  "Other",
];

const STYLES = [
  ["apa7", "APA 7"],
  ["mla9", "MLA 9"],
  ["harvard", "Harvard"],
  ["chicago", "Chicago"],
  ["ieee", "IEEE"],
];

const GOALS = [
  "Strengthen my thesis",
  "Improve argument and evidence",
  "Fix citations before submission",
  "Raise overall clarity and structure",
  "Prepare for a tight deadline",
];

const STEPS = ["Level", "Field", "Citations", "Goals", "First check"] as const;

export default function OnboardingPage() {
  const [step, setStep] = useState(0);
  const [level, setLevel] = useState("undergraduate");
  const [area, setArea] = useState(AREAS[0]);
  const [style, setStyle] = useState("apa7");
  const [goal, setGoal] = useState(GOALS[0]);

  const progress = useMemo(() => ((step + 1) / STEPS.length) * 100, [step]);

  function finish() {
    try {
      sessionStorage.setItem(
        "ac_onboarding",
        JSON.stringify({ level, area, style, goal, at: Date.now() }),
      );
    } catch {
      /* ignore */
    }
    window.location.href = "/check?onboarded=1";
  }

  return (
    <>
      <SiteHeader compact />
      <main id="main-content" tabIndex={-1} className="mx-auto max-w-xl px-4 py-12 md:py-16">
        <p className="text-sm font-medium tracking-wide text-[var(--teal)]">Welcome</p>
        <h1 className="mt-2 font-serif text-4xl">Set up your success workspace</h1>
        <p className="mt-3 text-sm leading-7 text-[var(--ink-muted)]">
          Two minutes. Then your first diagnostic check — no jargon gauntlet.
        </p>

        <div className="mt-8" aria-hidden>
          <div className="h-1.5 overflow-hidden rounded-full bg-[var(--rule)]">
            <div className="h-full rounded-full bg-[var(--teal)] transition-all duration-300" style={{ width: `${progress}%` }} />
          </div>
          <p className="mt-2 text-xs text-[var(--ink-muted)]">
            Step {step + 1} of {STEPS.length}: {STEPS[step]}
          </p>
        </div>

        <div className="ac-surface mt-8 p-6">
          {step === 0 && (
            <fieldset>
              <legend className="font-serif text-2xl">What’s your academic level?</legend>
              <div className="mt-5 grid gap-2">
                {LEVELS.map(([v, l]) => (
                  <label key={v} className={`ac-hit cursor-pointer justify-start rounded-[var(--radius-sm)] border px-4 text-sm ${level === v ? "border-[var(--teal)] bg-[var(--teal-soft)]" : "border-[var(--rule)]"}`}>
                    <input type="radio" className="sr-only" name="level" checked={level === v} onChange={() => setLevel(v)} />
                    {l}
                  </label>
                ))}
              </div>
            </fieldset>
          )}

          {step === 1 && (
            <fieldset>
              <legend className="font-serif text-2xl">What do you study?</legend>
              <div className="mt-5 grid gap-2 sm:grid-cols-2">
                {AREAS.map((a) => (
                  <label key={a} className={`ac-hit cursor-pointer justify-start rounded-[var(--radius-sm)] border px-4 text-sm ${area === a ? "border-[var(--teal)] bg-[var(--teal-soft)]" : "border-[var(--rule)]"}`}>
                    <input type="radio" className="sr-only" name="area" checked={area === a} onChange={() => setArea(a)} />
                    {a}
                  </label>
                ))}
              </div>
            </fieldset>
          )}

          {step === 2 && (
            <fieldset>
              <legend className="font-serif text-2xl">Preferred citation style</legend>
              <div className="mt-5 grid gap-2">
                {STYLES.map(([v, l]) => (
                  <label key={v} className={`ac-hit cursor-pointer justify-start rounded-[var(--radius-sm)] border px-4 text-sm ${style === v ? "border-[var(--teal)] bg-[var(--teal-soft)]" : "border-[var(--rule)]"}`}>
                    <input type="radio" className="sr-only" name="style" checked={style === v} onChange={() => setStyle(v)} />
                    {l}
                  </label>
                ))}
              </div>
            </fieldset>
          )}

          {step === 3 && (
            <fieldset>
              <legend className="font-serif text-2xl">What’s your main goal right now?</legend>
              <div className="mt-5 grid gap-2">
                {GOALS.map((g) => (
                  <label key={g} className={`ac-hit cursor-pointer justify-start rounded-[var(--radius-sm)] border px-4 text-sm ${goal === g ? "border-[var(--teal)] bg-[var(--teal-soft)]" : "border-[var(--rule)]"}`}>
                    <input type="radio" className="sr-only" name="goal" checked={goal === g} onChange={() => setGoal(g)} />
                    {g}
                  </label>
                ))}
              </div>
            </fieldset>
          )}

          {step === 4 && (
            <div>
              <h2 className="font-serif text-2xl">You’re ready for your first check</h2>
              <ul className="mt-4 space-y-2 text-sm leading-7 text-[var(--ink-muted)]">
                <li>
                  <strong className="text-[var(--ink)]">Level:</strong> {LEVELS.find((x) => x[0] === level)?.[1]}
                </li>
                <li>
                  <strong className="text-[var(--ink)]">Field:</strong> {area}
                </li>
                <li>
                  <strong className="text-[var(--ink)]">Citations:</strong> {STYLES.find((x) => x[0] === style)?.[1]}
                </li>
                <li>
                  <strong className="text-[var(--ink)]">Goal:</strong> {goal}
                </li>
              </ul>
              <p className="mt-4 text-sm leading-7 text-[var(--ink)]">
                Next you’ll paste a question and draft. We’ll pre-fill your level and citation style.
              </p>
            </div>
          )}
        </div>

        <div className="mt-8 flex flex-wrap items-center justify-between gap-3">
          <Button
            type="button"
            variant="ghost"
            disabled={step === 0}
            onClick={() => setStep((s) => Math.max(0, s - 1))}
          >
            Back
          </Button>
          {step < STEPS.length - 1 ? (
            <Button type="button" variant="primary" onClick={() => setStep((s) => Math.min(STEPS.length - 1, s + 1))}>
              Continue
            </Button>
          ) : (
            <Button type="button" variant="primary" onClick={finish}>
              Start first analysis
            </Button>
          )}
        </div>

        <p className="mt-6 text-sm text-[var(--ink-muted)]">
          Prefer to skip?{" "}
          <Link href="/app/dashboard" className="text-[var(--teal)] underline-offset-4 hover:underline">
            Go to dashboard
          </Link>
          {" · "}
          <Link href="/check" className="text-[var(--teal)] underline-offset-4 hover:underline">
            Jump to check
          </Link>
        </p>
      </main>
    </>
  );
}
