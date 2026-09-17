"use client";

import { Suspense, useMemo, useState } from "react";
import Link from "next/link";
import { AmbientStage } from "@/components/AmbientStage";
import { useAuth } from "@/components/AuthProvider";
import { EmailVerifyBanner } from "@/components/EmailVerifyBanner";
import { SiteHeader } from "@/components/SiteHeader";
import { SignupConversionBeacon } from "@/components/SignupConversionBeacon";
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
  const { user, signedIn, needsVerify } = useAuth();
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
    window.location.href = "/app/dashboard";
  }

  return (
    <>
      <SiteHeader compact />
      <Suspense fallback={null}>
        <SignupConversionBeacon />
      </Suspense>
      <AmbientStage className="min-h-[calc(100dvh-3.5rem)]">
        <main id="main-content" tabIndex={-1} className="mx-auto max-w-xl px-4 py-12 md:py-16">
          <div className="ac-auth-panel ac-surface relative overflow-hidden p-6 md:p-8">
            <div className="ac-auth-panel-shine pointer-events-none absolute inset-0" aria-hidden />
            <p className="ac-enter relative text-sm font-medium tracking-wide text-[var(--teal)]">
              {signedIn ? "You’re signed in" : "Welcome"}
            </p>
            <h1 className="ac-enter ac-enter-delay-1 relative mt-2 font-serif text-4xl">
              Set up your success workspace
            </h1>
            <p className="ac-enter ac-enter-delay-2 relative mt-3 text-sm leading-7 text-[var(--ink-muted)]">
              {signedIn
                ? `Account ready${user?.email ? ` for ${user.email}` : ""}. Two minutes here, then your dashboard.`
                : "Two minutes. Then your first diagnostic check — no jargon gauntlet."}
            </p>
            {needsVerify ? (
              <div className="relative mt-6">
                <EmailVerifyBanner email={user?.pending_email || user?.email || ""} />
              </div>
            ) : null}

            <div className="ac-enter ac-enter-delay-3 relative mt-8" aria-hidden>
              <div className="h-1.5 overflow-hidden rounded-full bg-[var(--rule)]">
                <div
                  className="h-full rounded-full bg-[var(--teal)] transition-all duration-500 ease-out"
                  style={{ width: `${progress}%` }}
                />
              </div>
              <p className="mt-2 text-xs text-[var(--ink-muted)]">
                Step {step + 1} of {STEPS.length}: {STEPS[step]}
              </p>
            </div>

            <div className="ac-enter ac-enter-delay-3 relative mt-8">
              {step === 0 && (
                <fieldset>
                  <legend className="font-serif text-2xl">What’s your academic level?</legend>
                  <div className="mt-4 grid gap-2">
                    {LEVELS.map(([value, label]) => (
                      <label
                        key={value}
                        className="flex cursor-pointer items-center gap-3 rounded-md border border-[var(--rule)] px-3 py-2.5 has-[:checked]:border-[var(--teal)]"
                      >
                        <input
                          type="radio"
                          name="level"
                          value={value}
                          checked={level === value}
                          onChange={() => setLevel(value)}
                        />
                        <span className="text-sm">{label}</span>
                      </label>
                    ))}
                  </div>
                </fieldset>
              )}
              {step === 1 && (
                <fieldset>
                  <legend className="font-serif text-2xl">Which field are you writing in?</legend>
                  <div className="mt-4 grid gap-2">
                    {AREAS.map((item) => (
                      <label
                        key={item}
                        className="flex cursor-pointer items-center gap-3 rounded-md border border-[var(--rule)] px-3 py-2.5 has-[:checked]:border-[var(--teal)]"
                      >
                        <input
                          type="radio"
                          name="area"
                          value={item}
                          checked={area === item}
                          onChange={() => setArea(item)}
                        />
                        <span className="text-sm">{item}</span>
                      </label>
                    ))}
                  </div>
                </fieldset>
              )}
              {step === 2 && (
                <fieldset>
                  <legend className="font-serif text-2xl">Preferred citation style?</legend>
                  <div className="mt-4 grid gap-2">
                    {STYLES.map(([value, label]) => (
                      <label
                        key={value}
                        className="flex cursor-pointer items-center gap-3 rounded-md border border-[var(--rule)] px-3 py-2.5 has-[:checked]:border-[var(--teal)]"
                      >
                        <input
                          type="radio"
                          name="style"
                          value={value}
                          checked={style === value}
                          onChange={() => setStyle(value)}
                        />
                        <span className="text-sm">{label}</span>
                      </label>
                    ))}
                  </div>
                </fieldset>
              )}
              {step === 3 && (
                <fieldset>
                  <legend className="font-serif text-2xl">What’s your main goal right now?</legend>
                  <div className="mt-4 grid gap-2">
                    {GOALS.map((item) => (
                      <label
                        key={item}
                        className="flex cursor-pointer items-center gap-3 rounded-md border border-[var(--rule)] px-3 py-2.5 has-[:checked]:border-[var(--teal)]"
                      >
                        <input
                          type="radio"
                          name="goal"
                          value={item}
                          checked={goal === item}
                          onChange={() => setGoal(item)}
                        />
                        <span className="text-sm">{item}</span>
                      </label>
                    ))}
                  </div>
                </fieldset>
              )}
              {step === 4 && (
                <div>
                  <h2 className="font-serif text-2xl">You’re ready for your first check</h2>
                  <p className="mt-4 text-sm leading-7 text-[var(--ink)]">
                    Next you’ll land on your dashboard — signed in — then you can run your first check anytime.
                  </p>
                </div>
              )}
            </div>

            <div className="relative mt-8 flex flex-wrap items-center justify-between gap-3">
              <Button
                type="button"
                variant="ghost"
                disabled={step === 0}
                onClick={() => setStep((s) => Math.max(0, s - 1))}
              >
                Back
              </Button>
              {step < STEPS.length - 1 ? (
                <Button
                  type="button"
                  variant="primary"
                  className="ac-cta-glow"
                  onClick={() => setStep((s) => Math.min(STEPS.length - 1, s + 1))}
                >
                  Continue
                </Button>
              ) : (
                <Button type="button" variant="primary" className="ac-cta-glow" onClick={finish}>
                  Go to dashboard
                </Button>
              )}
            </div>

            <p className="relative mt-6 text-sm text-[var(--ink-muted)]">
              Prefer to skip?{" "}
              <Link href="/app/dashboard" className="text-[var(--teal)] underline-offset-4 hover:underline">
                Go to dashboard
              </Link>
              {" · "}
              <Link href="/check" className="text-[var(--teal)] underline-offset-4 hover:underline">
                Jump to check
              </Link>
            </p>
          </div>
        </main>
      </AmbientStage>
    </>
  );
}
