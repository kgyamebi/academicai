"use client";

import { useEffect, useId, useRef, useState } from "react";
import { animateValue, easeInOutCubic, prefersReducedMotion } from "@/lib/motion";

export function ScoreRing({
  score,
  label,
  size = "lg",
  animateOnMount = true,
  playKey,
  onDisplayChange,
  compactLabel = false,
}: {
  score: number;
  label?: string;
  size?: "sm" | "md" | "lg";
  /** Orchestrated count-up + ring draw on mount / playKey change. */
  animateOnMount?: boolean;
  playKey?: string | number;
  /** Sync external Overall Score (or other UI) to the same count-up. */
  onDisplayChange?: (value: number) => void;
  /** Hide the side copy when the parent already shows Overall Score. */
  compactLabel?: boolean;
}) {
  const gradId = useId();
  const glowId = useId();
  const target = Math.max(0, Math.min(100, Math.round(score)));
  const dims = { sm: 72, md: 96, lg: 140 }[size];
  const stroke = size === "sm" ? 6 : size === "md" ? 8 : 11;
  const r = (dims - stroke) / 2;
  const c = 2 * Math.PI * r;
  const fontSize = size === "lg" ? "2.05rem" : size === "md" ? "1.5rem" : "1.15rem";

  const [display, setDisplay] = useState(animateOnMount ? 0 : target);
  const [veil, setVeil] = useState(false);
  const [landing, setLanding] = useState(false);
  const [pulse, setPulse] = useState(false);
  const playedKey = useRef<string | number | null>(null);
  const onDisplayChangeRef = useRef(onDisplayChange);
  onDisplayChangeRef.current = onDisplayChange;

  useEffect(() => {
    if (!animateOnMount || prefersReducedMotion()) {
      setDisplay(target);
      onDisplayChangeRef.current?.(target);
      return;
    }

    const key = playKey ?? "mount";
    if (playedKey.current === key && playKey === undefined) {
      setDisplay(target);
      onDisplayChangeRef.current?.(target);
      return;
    }
    playedKey.current = key;

    setDisplay(0);
    onDisplayChangeRef.current?.(0);
    setVeil(true);
    setLanding(false);
    setPulse(false);

    let stopAnim: (() => void) | undefined;
    const pause = window.setTimeout(() => {
      setVeil(false);
      stopAnim = animateValue({
        from: 0,
        to: target,
        duration: 1450,
        ease: easeInOutCubic,
        onUpdate: (v) => {
          const n = Math.round(v);
          setDisplay(n);
          onDisplayChangeRef.current?.(n);
        },
        onComplete: () => {
          setLanding(true);
          setPulse(true);
          window.setTimeout(() => setPulse(false), 900);
          window.setTimeout(() => setLanding(false), 560);
        },
      });
    }, 220);

    return () => {
      window.clearTimeout(pause);
      stopAnim?.();
    };
  }, [target, animateOnMount, playKey]);

  const progress = display / 100;
  const offset = c - progress * c;
  const tone =
    target >= 75 ? "var(--forest)" : target >= 55 ? "var(--teal)" : target >= 40 ? "var(--amber)" : "var(--crimson)";

  // Leading-edge tip in SVG space (circle starts at 3 o'clock; parent SVG is -rotate-90).
  const tipAngle = progress * Math.PI * 2;
  const tipX = dims / 2 + Math.cos(tipAngle) * r;
  const tipY = dims / 2 + Math.sin(tipAngle) * r;

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
          <defs>
            <linearGradient id={gradId} x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor={tone} stopOpacity="0.85" />
              <stop offset="100%" stopColor={tone} stopOpacity="1" />
            </linearGradient>
            <filter id={glowId} x="-40%" y="-40%" width="180%" height="180%">
              <feGaussianBlur stdDeviation="2.2" result="blur" />
              <feMerge>
                <feMergeNode in="blur" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
          </defs>
          <circle cx={dims / 2} cy={dims / 2} r={r} fill="none" stroke="var(--rule)" strokeWidth={stroke} />
          <circle
            cx={dims / 2}
            cy={dims / 2}
            r={r}
            fill="none"
            stroke={`url(#${gradId})`}
            strokeWidth={stroke}
            strokeLinecap="round"
            strokeDasharray={c}
            strokeDashoffset={offset}
            filter={`url(#${glowId})`}
          />
          {progress > 0.02 && progress < 0.995 ? (
            <circle
              cx={tipX}
              cy={tipY}
              r={stroke * 0.55}
              fill={tone}
              className="ac-score-trail"
              style={{ filter: `url(#${glowId})` }}
            />
          ) : null}
        </svg>
        <div className="absolute inset-0 grid place-items-center">
          <span className="font-serif tabular-nums tracking-tight text-[var(--ink)]" style={{ fontSize }}>
            {display}
          </span>
        </div>
      </div>
      {!compactLabel ? (
        <div className="min-w-0">
          <p className="text-sm font-medium uppercase tracking-wide text-[var(--ink-muted)]">
            {label || "Academic health"}
          </p>
          <p className="mt-1 max-w-xs text-sm leading-6 text-[var(--ink-muted)]">
            AI-assisted diagnostic indicator — not an official grade.
          </p>
        </div>
      ) : null}
    </div>
  );
}
