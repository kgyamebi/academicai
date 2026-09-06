"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";

const links = [
  { href: "/features", label: "Features" },
  { href: "/pricing", label: "Pricing" },
  { href: "/blog", label: "Guides" },
  { href: "/help", label: "Help" },
];

export function SiteHeader({ compact = false }: { compact?: boolean }) {
  const path = usePathname();
  const [open, setOpen] = useState(false);
  return (
    <header className="border-b border-[var(--rule)] bg-[var(--paper-2)]/90 backdrop-blur">
      <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-4 py-3">
        <Link href="/" className="font-serif text-xl tracking-tight text-[var(--ink)]">
          AcademicCheck <span className="text-[var(--teal)]">AI</span>
        </Link>
        {!compact && (
          <nav className="hidden items-center gap-6 text-sm md:flex" aria-label="Primary">
            {links.map((l) => (
              <Link
                key={l.href}
                href={l.href}
                aria-current={path === l.href ? "page" : undefined}
                className="text-[var(--ink-muted)] hover:text-[var(--teal)]"
              >
                {l.label}
              </Link>
            ))}
          </nav>
        )}
        <div className="flex items-center gap-2 text-sm">
          {!compact && (
            <button
              type="button"
              className="rounded-md px-3 py-1.5 md:hidden"
              aria-expanded={open}
              aria-controls="mobile-nav"
              onClick={() => setOpen((value) => !value)}
            >
              Menu
            </button>
          )}
          <Link href="/login" className="rounded-md px-3 py-1.5 hover:bg-black/5">
            Sign in
          </Link>
          <Link
            href="/check"
            className="rounded-md bg-[var(--teal)] px-3 py-1.5 text-white hover:bg-[var(--teal-2)]"
          >
            Check assignment
          </Link>
        </div>
      </div>
      {!compact && open && (
        <nav id="mobile-nav" className="space-y-1 border-t border-[var(--rule)] px-4 py-3 md:hidden" aria-label="Mobile">
          {links.map((l) => (
            <Link
              key={l.href}
              href={l.href}
              aria-current={path === l.href ? "page" : undefined}
              className="block rounded-md px-3 py-2 text-[var(--ink)] hover:bg-black/5"
              onClick={() => setOpen(false)}
            >
              {l.label}
            </Link>
          ))}
        </nav>
      )}
    </header>
  );
}
