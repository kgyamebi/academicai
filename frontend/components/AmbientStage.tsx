"use client";

import type { ReactNode } from "react";

/**
 * Ambient stage — quiet paper atmosphere with one intentional light sweep.
 */
export function AmbientStage({
  children,
  className = "",
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <div className={`relative isolate overflow-hidden ${className}`}>
      <div className="ac-ambient pointer-events-none absolute inset-0" aria-hidden>
        <div className="ac-ambient-grid" />
        <div className="ac-ambient-sweep" />
      </div>
      <div className="relative z-10">{children}</div>
    </div>
  );
}

/** Auth panel — staggered settle that feels expensive, not busy. */
export function AuthShell({
  children,
  eyebrow,
  title,
  subtitle,
}: {
  children: ReactNode;
  eyebrow?: string;
  title: string;
  subtitle?: string;
}) {
  return (
    <AmbientStage className="min-h-[calc(100dvh-3.5rem)]">
      <div className="mx-auto flex max-w-md flex-col justify-center px-4 py-14 md:py-20">
        <div className="ac-auth-panel ac-surface relative overflow-hidden p-6 md:p-8">
          <div className="ac-auth-panel-shine pointer-events-none absolute inset-0" aria-hidden />
          <div className="ac-auth-panel-sweep pointer-events-none absolute inset-0" aria-hidden />
          {eyebrow ? (
            <p className="ac-settle relative text-sm font-medium tracking-wide text-[var(--teal)]">{eyebrow}</p>
          ) : null}
          <h1
            className={`ac-settle ac-settle-d1 relative font-serif text-3xl tracking-tight text-[var(--ink)] md:text-4xl ${eyebrow ? "mt-2" : ""}`}
          >
            {title}
          </h1>
          {subtitle ? (
            <p className="ac-settle ac-settle-d2 relative mt-3 text-sm leading-7 text-[var(--ink-muted)]">{subtitle}</p>
          ) : null}
          <div className="ac-settle ac-settle-d3 relative mt-8">{children}</div>
        </div>
      </div>
    </AmbientStage>
  );
}
