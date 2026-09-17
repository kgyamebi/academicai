"use client";

import type { ReactNode } from "react";

/**
 * Static ambient stage — paper atmosphere only.
 * No drifting orbs, sheen, or decorative loops.
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
      </div>
      <div className="relative z-10">{children}</div>
    </div>
  );
}

/** Auth / onboarding panel with one quiet settle. */
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
          {eyebrow ? (
            <p className="relative text-sm font-medium tracking-wide text-[var(--teal)]">{eyebrow}</p>
          ) : null}
          <h1
            className={`relative font-serif text-3xl tracking-tight text-[var(--ink)] md:text-4xl ${eyebrow ? "mt-2" : ""}`}
          >
            {title}
          </h1>
          {subtitle ? (
            <p className="relative mt-3 text-sm leading-7 text-[var(--ink-muted)]">{subtitle}</p>
          ) : null}
          <div className="relative mt-8">{children}</div>
        </div>
      </div>
    </AmbientStage>
  );
}
