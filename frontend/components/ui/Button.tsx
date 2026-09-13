import Link from "next/link";
import { forwardRef, type ButtonHTMLAttributes, type ReactNode } from "react";
import { cn } from "@/lib/utils";

type Variant = "primary" | "secondary" | "ghost" | "danger";

const styles: Record<Variant, string> = {
  primary:
    "bg-[var(--teal)] text-white hover:bg-[var(--teal-2)] disabled:opacity-60 shadow-[var(--shadow-1)]",
  secondary:
    "border border-[var(--rule)] bg-[var(--paper-2)] text-[var(--ink)] hover:bg-black/[0.03] disabled:opacity-60",
  ghost: "text-[var(--ink-muted)] hover:bg-black/[0.04] hover:text-[var(--ink)] disabled:opacity-60",
  danger: "bg-[var(--crimson)] text-white hover:opacity-90 disabled:opacity-60",
};

export const Button = forwardRef<
  HTMLButtonElement,
  ButtonHTMLAttributes<HTMLButtonElement> & { variant?: Variant; busy?: boolean }
>(function Button({ variant = "primary", className, children, busy, type = "button", ...props }, ref) {
  return (
    <button
      {...props}
      ref={ref}
      type={type}
      aria-busy={busy || undefined}
      disabled={props.disabled || busy}
      className={cn(
        "ac-hit inline-flex gap-2 rounded-[var(--radius-sm)] px-4 text-sm font-medium transition-colors duration-150",
        styles[variant],
        className,
      )}
    >
      {busy ? "Working…" : children}
    </button>
  );
});

export function ButtonLink({
  href,
  variant = "primary",
  className,
  children,
}: {
  href: string;
  variant?: Variant;
  className?: string;
  children: ReactNode;
}) {
  return (
    <Link
      href={href}
      className={cn(
        "ac-hit inline-flex gap-2 rounded-[var(--radius-sm)] px-4 text-sm font-medium transition-colors duration-150",
        styles[variant],
        className,
      )}
    >
      {children}
    </Link>
  );
}
