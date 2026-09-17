"use client";

import { useEffect, useRef, useState } from "react";
import { animateValue, easeInOutCubic, prefersReducedMotion } from "@/lib/motion";

export function ScoreRing({
  score,
  label,
  size = "lg",
  animateOnMount = true,
  playKey,
}: {
  score: number;
  label?: string;
  size?: "sm" | "md" | "lg";
  /** Orchestrated count-up + ring draw on mount / playKey change. */
  animateOnMount?: boolean;
  playKey?: string | number;
}) {
  const target = Math.max(0, Math.min(100, Math.round(score)));
  const dims = { sm: 72, md: 96, lg: 128 }[size];
  const stroke = size === "sm" ? 6 : size === "md" ? 8 : 10;
  const r = (dims - stroke) / 2;
  const c = 2 * Math.PI * r;
  const fontSize = size === "lg" ? "1.875rem" : size === "md" ? "1.5rem" : "1.15rem";

  const [display, setDisplay] = useState(animateOnMount ? 0 : target);
  const [veil, setVeil] = useState(false);
  const [landing, setLanding] = useState(false);
  const [pulse, setPulse] = useState(false);
  const playedKey = useRef<string | number | null>(null);

  useEffect(() => {
    if (!animateOnMount || prefersReducedMotion()) {
      setDisplay(target);
      return;
    }

    const key = playKey ?? "mount";
    if (playedKey.current === key && playKey === undefined) {
      setDisplay(target);
      return;
    }
    playedKey.current = key;

    setDisplay(0);
    setVeil(true);
    setLanding(false);
    setPulse(false);

    let stopAnim: (() => void) | undefined;
    const pause = window.setTimeout(() => {
      setVeil(false);
      stopAnim = animateValue({
        from: 0,
        to: target,
        duration: 1200,
        ease: easeInOutCubic,
        onUpdate: (v) => setDisplay(Math.round(v)),
        onComplete: () => {
          setLanding(true);
          setPulse(true);
          window.setTimeout(() => setPulse(false), 720);
          window.setTimeout(() => setLanding(false), 500);
        },
      });
    }, 180);

    return () => {
      window.clearTimeout(pause);
      stopAnim?.();
    };
  }, [target, animateOnMount, playKey]);

  const offset = c - (display / 100) * c;
  const tone =
    target >= 75 ? "var(--forest)" : target >= 55 ? "var(--teal)" : target >= 40 ? "var(--amber)" : "var(--crimson)";

  return (
    <div className="relative flex items-center gap-5">
      <div className={`ac-dim-veil${veil ? " is-on" : ""}`} aria-hidden />
      <div
        className={`ac-score-ring-wrap relative${landing ? " is-landing" : ""}${pulse ? " is-pulse" : ""}`}
        style={{ width: dims, height: dims }}
        role="img"
        aria-label={`Diagnostic score ${target} out of 100`}
      >
        <svg width={dims} height={dims} className="-rotate-90" aria-hidden>
          <circle cx={dims / 2} cy={dims / 2} r={r} fill="none" stroke="var(--rule)" strokeWidth={stroke} />
          <circle
            cx={dims / 2}
            cy={dims / 2}
            r={r}
            fill="none"
            stroke={tone}
            strokeWidth={stroke}
            strokeLinecap="round"
            strokeDasharray={c}
            strokeDashoffset={offset}
            style={{ filter: "drop-shadow(0 0 6px rgba(15, 118, 110, 0.18))" }}
          />
        </svg>
        <div className="absolute inset-0 grid place-items-center">
          <span className="font-serif tabular-nums text-[var(--ink)]" style={{ fontSize }}>
            {display}
          </span>
        </div>
      </div>
      <div className="min-w-0">
        <p className="text-sm font-medium uppercase tracking-wide text-[var(--ink-muted)]">
          {label || "Academic health"}
        </p>
        <p className="mt-1 max-w-xs text-sm leading-6 text-[var(--ink-muted)]">
          AI-assisted diagnostic indicator — not an official grade.
        </p>
      </div>
    </div>
  );
}
