"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { ButtonLink } from "@/components/ui/Button";

const links = [
  { href: "/sample-report", label: "Sample report" },
  { href: "/pricing", label: "Pricing" },
  { href: "/about", label: "About" },
  { href: "/help", label: "Help" },
  { href: "/contact", label: "Contact" },
];

export function SiteHeader({ compact = false }: { compact?: boolean }) {
  const path = usePathname();
  const [open, setOpen] = useState(false);
  const menuButtonRef = useRef<HTMLButtonElement>(null);
  const firstLinkRef = useRef<HTMLAnchorElement>(null);

  useEffect(() => {
    if (!open) return;
    firstLinkRef.current?.focus();
    function onKey(event: KeyboardEvent) {
      if (event.key === "Escape") {
        setOpen(false);
        menuButtonRef.current?.focus();
      }
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open]);

  return (
    <header className="sticky top-0 z-40 border-b border-[var(--rule)]/80 bg-[var(--paper-2)]/85 backdrop-blur-md">
      <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-4 py-3">
        <Link href="/" className="font-serif text-xl tracking-tight text-[var(--ink)]">
          AcademicCheck <span className="text-[var(--teal)]">AI</span>
        </Link>
        {!compact && (
          <nav className="hidden items-center gap-7 text-sm md:flex" aria-label="Primary">
            {links.map((l) => (
              <Link
                key={l.href}
                href={l.href}
                aria-current={path === l.href ? "page" : undefined}
                className="ac-hit px-1 text-[var(--ink-muted)] transition-colors hover:text-[var(--ink)]"
              >
                {l.label}
              </Link>
            ))}
          </nav>
        )}
        <div className="flex items-center gap-2 text-sm">
          {!compact && (
            <button
              ref={menuButtonRef}
              type="button"
              className="ac-hit rounded-[var(--radius-sm)] px-3 md:hidden"
              aria-expanded={open}
              aria-controls="mobile-nav"
              aria-haspopup="true"
              aria-label={open ? "Close menu" : "Open menu"}
              onClick={() => setOpen((value) => !value)}
            >
              Menu
            </button>
          )}
          <Link href="/login" className="ac-hit hidden rounded-[var(--radius-sm)] px-3 text-[var(--ink-muted)] hover:text-[var(--ink)] sm:inline-flex">
            Sign in
          </Link>
          <ButtonLink href="/check" variant="primary" className="px-3.5">
            Check assignment
          </ButtonLink>
        </div>
      </div>
      {!compact && open && (
        <nav id="mobile-nav" className="space-y-1 border-t border-[var(--rule)] px-4 py-3 md:hidden" aria-label="Mobile">
          {links.map((l, index) => (
            <Link
              key={l.href}
              ref={index === 0 ? firstLinkRef : undefined}
              href={l.href}
              className="ac-hit justify-start rounded-[var(--radius-sm)] px-3 text-[var(--ink)]"
              onClick={() => setOpen(false)}
            >
              {l.label}
            </Link>
          ))}
          <Link href="/login" className="ac-hit justify-start rounded-[var(--radius-sm)] px-3" onClick={() => setOpen(false)}>
            Sign in
          </Link>
        </nav>
      )}
    </header>
  );
}
