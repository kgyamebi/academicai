import { type ReactNode } from "react";
import { cn } from "@/lib/utils";
import { ButtonLink } from "./Button";

export function EmptyState({
  title,
  body,
  actionHref,
  actionLabel,
  className,
  kicker,
}: {
  title: string;
  body: string;
  actionHref?: string;
  actionLabel?: string;
  className?: string;
  kicker?: string;
}) {
  return (
    <div
      role="status"
      className={cn(
        "flex flex-col items-start gap-3 rounded-[var(--radius-md)] border border-dashed border-[var(--rule)] bg-[var(--paper-2)] px-5 py-8 md:px-8 md:py-10",
        className,
      )}
    >
      {kicker ? <p className="text-sm font-medium tracking-wide text-[var(--teal)]">{kicker}</p> : null}
      <h3 className="font-serif text-xl text-[var(--ink)] md:text-2xl">{title}</h3>
      <p className="max-w-md text-sm leading-7 text-[var(--ink-muted)]">{body}</p>
      {actionHref && actionLabel ? (
        <ButtonLink href={actionHref} variant="primary" className="mt-1">
          {actionLabel}
        </ButtonLink>
      ) : null}
    </div>
  );
}

export function Skeleton({ className }: { className?: string }) {
  return <div className={cn("ac-skeleton h-4 w-full", className)} aria-hidden />;
}

export function SkeletonBlock({ lines = 3 }: { lines?: number }) {
  return (
    <div className="space-y-3" aria-busy="true" aria-live="polite">
      <span className="sr-only">Loading…</span>
      {Array.from({ length: lines }).map((_, i) => (
        <Skeleton key={i} className={i === lines - 1 ? "w-2/3" : "w-full"} />
      ))}
    </div>
  );
}

export function StatusBanner({
  children,
  tone = "neutral",
}: {
  children: ReactNode;
  tone?: "neutral" | "success" | "warn";
}) {
  const tones = {
    neutral: "border-[var(--rule)] bg-[var(--paper-2)] text-[var(--ink)]",
    success: "border-[var(--forest)]/25 bg-[var(--teal-soft)] text-[var(--forest)]",
    warn: "border-[var(--amber)]/30 bg-amber-50 text-[var(--amber)]",
  };
  return (
    <p aria-live="polite" className={cn("rounded-[var(--radius-sm)] border px-3 py-3 text-sm", tones[tone])}>
      {children}
    </p>
  );
}
