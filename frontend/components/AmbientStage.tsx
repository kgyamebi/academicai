"use client";

import type { ReactNode } from "react";

/**
 * Full-bleed ambient stage: soft teal/ink orbs, slow sheen, paper grid.
 * Motion is intentional and calm — respects prefers-reduced-motion via CSS.
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
        <div className="ac-orb ac-orb-a" />
        <div className="ac-orb ac-orb-b" />
        <div className="ac-orb ac-orb-c" />
        <div className="ac-ambient-grid" />
        <div className="ac-ambient-sheen" />
      </div>
      <div className="relative z-10">{children}</div>
    </div>
  );
}

/** Auth / onboarding panel with staggered entrance. */
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
            <p className="ac-enter relative text-sm font-medium tracking-wide text-[var(--teal)]">{eyebrow}</p>
          ) : null}
          <h1
            className={`ac-enter ac-enter-delay-1 relative font-serif text-3xl tracking-tight text-[var(--ink)] md:text-4xl ${eyebrow ? "mt-2" : ""}`}
          >
            {title}
          </h1>
          {subtitle ? (
            <p className="ac-enter ac-enter-delay-2 relative mt-3 text-sm leading-7 text-[var(--ink-muted)]">
              {subtitle}
            </p>
          ) : null}
          <div className="ac-enter ac-enter-delay-3 relative mt-8">{children}</div>
        </div>
      </div>
    </AmbientStage>
  );
}
