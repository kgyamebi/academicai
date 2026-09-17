"use client";

import { useEffect, useRef, useState, type ReactNode } from "react";
import { animateValue, easeOutExpo } from "@/lib/motion";
import { cn } from "@/lib/utils";

export function AnimatedNumber({
  value,
  className,
  suffix = "",
  duration = 900,
}: {
  value: number;
  className?: string;
  suffix?: string;
  duration?: number;
}) {
  const [display, setDisplay] = useState(0);

  useEffect(() => {
    return animateValue({
      from: 0,
      to: value,
      duration,
      ease: easeOutExpo,
      onUpdate: (v) => setDisplay(Math.round(v)),
    });
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
  const pathRef = useRef<SVGPolylineElement>(null);
  const [drawn, setDrawn] = useState(false);
  const [pointsVisible, setPointsVisible] = useState(0);

  useEffect(() => {
    const el = pathRef.current;
    if (!el || !values.length) return;
    const length = el.getTotalLength?.() ?? 0;
    if (length > 0) {
      el.style.strokeDasharray = `${length}`;
      el.style.strokeDashoffset = `${length}`;
      requestAnimationFrame(() => {
        el.style.transition = "stroke-dashoffset 900ms var(--ease-out-expo)";
        el.style.strokeDashoffset = "0";
      });
    }
    setDrawn(true);
    values.forEach((_, i) => {
      window.setTimeout(() => setPointsVisible(i + 1), 200 + i * 160);
    });
  }, [values]);

  if (!values.length) return null;
  const max = Math.max(...values, 1);
  const min = Math.min(...values, 0);
  const span = Math.max(1, max - min);
  const w = 160;
  const h = 48;
  const pts = values.map((v, i) => {
    const x = values.length === 1 ? w / 2 : (i / (values.length - 1)) * w;
    const y = h - ((v - min) / span) * (h - 8) - 4;
    return { x, y, v };
  });
  const points = pts.map((p) => `${p.x},${p.y}`).join(" ");
  const improvement = values.length > 1 ? Math.round(values[values.length - 1]! - values[0]!) : 0;

  return (
    <div className={cn("relative", className)}>
      <svg viewBox={`0 0 ${w} ${h}`} className="w-full" role="img" aria-label="Score trend chart">
        <polyline
          ref={pathRef}
          fill="none"
          stroke="var(--teal)"
          strokeWidth="2.5"
          strokeLinecap="round"
          strokeLinejoin="round"
          points={points}
        />
        {pts.map((p, i) => (
          <circle
            key={`${p.v}-${i}`}
            cx={p.x}
            cy={p.y}
            r="2.5"
            fill="var(--teal)"
            style={{
              opacity: i < pointsVisible ? 1 : 0,
              transition: "opacity 280ms var(--ease-out)",
            }}
          />
        ))}
      </svg>
      {drawn && improvement > 0 ? (
        <p className="ac-settle mt-1 text-xs font-medium text-[var(--forest)]">+{improvement} pts</p>
      ) : null}
    </div>
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
