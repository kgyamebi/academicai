"use client";

import { useEffect, useState, type ReactNode } from "react";
import { cn } from "@/lib/utils";

export function AnimatedNumber({
  value,
  className,
  suffix = "",
  duration = 700,
}: {
  value: number;
  className?: string;
  suffix?: string;
  duration?: number;
}) {
  const [display, setDisplay] = useState(0);

  useEffect(() => {
    const reduce =
      typeof window !== "undefined" && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (reduce) {
      setDisplay(value);
      return;
    }
    let frame = 0;
    const start = performance.now();
    const from = 0;
    const tick = (now: number) => {
      const t = Math.min(1, (now - start) / duration);
      const eased = 1 - Math.pow(1 - t, 3);
      setDisplay(Math.round(from + (value - from) * eased));
      if (t < 1) frame = requestAnimationFrame(tick);
    };
    frame = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(frame);
  }, [value, duration]);

  return (
    <span className={cn("tabular-nums", className)}>
      {display}
      {suffix}
    </span>
  );
}

export function TrendPill({ delta, label }: { delta: number | null | undefined; label?: string }) {
  if (delta == null) {
    return (
      <span className="inline-flex items-center rounded-full border border-[var(--rule)] px-2.5 py-0.5 text-xs text-[var(--ink-muted)]">
        {label || "Building trend"}
      </span>
    );
  }
  const up = delta >= 0;
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-medium",
        up ? "bg-[var(--teal-soft)] text-[var(--forest)]" : "bg-red-50 text-[var(--crimson)]",
      )}
    >
      <span aria-hidden>{up ? "↑" : "↓"}</span>
      {up ? "+" : ""}
      {delta}%{label ? ` ${label}` : ""}
    </span>
  );
}

export function MiniRing({
  score,
  size = 56,
  label,
}: {
  score: number;
  size?: number;
  label: string;
}) {
  const clamped = Math.max(0, Math.min(100, Math.round(score)));
  const stroke = 5;
  const r = (size - stroke) / 2;
  const c = 2 * Math.PI * r;
  const offset = c - (clamped / 100) * c;
  const tone =
    clamped >= 75 ? "var(--forest)" : clamped >= 55 ? "var(--teal)" : clamped >= 40 ? "var(--amber)" : "var(--crimson)";

  return (
    <div className="flex flex-col items-center gap-2">
      <div className="relative" style={{ width: size, height: size }} role="img" aria-label={`${label}: ${clamped} out of 100`}>
        <svg width={size} height={size} className="-rotate-90" aria-hidden>
          <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="var(--rule)" strokeWidth={stroke} />
          <circle
            cx={size / 2}
            cy={size / 2}
            r={r}
            fill="none"
            stroke={tone}
            strokeWidth={stroke}
            strokeLinecap="round"
            strokeDasharray={c}
            strokeDashoffset={offset}
            className="transition-[stroke-dashoffset] duration-700 ease-out"
          />
        </svg>
        <div className="absolute inset-0 grid place-items-center">
          <span className="font-serif text-sm tabular-nums">{clamped}</span>
        </div>
      </div>
      <p className="max-w-[5.5rem] text-center text-[11px] leading-4 text-[var(--ink-muted)]">{label}</p>
    </div>
  );
}

export function ProgressBar({ value, tone }: { value: number; tone?: string }) {
  const clamped = Math.max(0, Math.min(100, value));
  const color =
    tone ||
    (clamped >= 75 ? "var(--forest)" : clamped >= 55 ? "var(--teal)" : clamped >= 40 ? "var(--amber)" : "var(--crimson)");
  return (
    <div className="h-1.5 overflow-hidden rounded-full bg-[var(--rule)]" aria-hidden>
      <div
        className="h-full rounded-full transition-all duration-700 ease-out"
        style={{ width: `${clamped}%`, background: color }}
      />
    </div>
  );
}

export function Sparkline({ values, className }: { values: number[]; className?: string }) {
  if (!values.length) return null;
  const max = Math.max(...values, 1);
  const min = Math.min(...values, 0);
  const span = Math.max(1, max - min);
  const w = 160;
  const h = 48;
  const points = values
    .map((v, i) => {
      const x = values.length === 1 ? w / 2 : (i / (values.length - 1)) * w;
      const y = h - ((v - min) / span) * (h - 8) - 4;
      return `${x},${y}`;
    })
    .join(" ");

  return (
    <svg viewBox={`0 0 ${w} ${h}`} className={cn("w-full", className)} role="img" aria-label="Score trend chart">
      <polyline
        fill="none"
        stroke="var(--teal)"
        strokeWidth="2.5"
        strokeLinecap="round"
        strokeLinejoin="round"
        points={points}
      />
      {values.map((v, i) => {
        const x = values.length === 1 ? w / 2 : (i / (values.length - 1)) * w;
        const y = h - ((v - min) / span) * (h - 8) - 4;
        return <circle key={`${v}-${i}`} cx={x} cy={y} r="2.5" fill="var(--teal)" />;
      })}
    </svg>
  );
}

export function SectionHeading({
  id,
  title,
  subtitle,
  action,
}: {
  id: string;
  title: string;
  subtitle?: string;
  action?: ReactNode;
}) {
  return (
    <div className="flex flex-wrap items-end justify-between gap-3">
      <div>
        <h2 id={id} className="font-serif text-2xl text-[var(--ink)]">
          {title}
        </h2>
        {subtitle ? <p className="mt-1 text-sm text-[var(--ink-muted)]">{subtitle}</p> : null}
      </div>
      {action}
    </div>
  );
}
