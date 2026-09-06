import Link from "next/link";

const links = [
  { href: "/features", label: "Features" },
  { href: "/pricing", label: "Pricing" },
  { href: "/blog", label: "Guides" },
  { href: "/help", label: "Help" },
];

export function SiteHeader({ compact = false }: { compact?: boolean }) {
  return (
    <header className="border-b border-[var(--rule)] bg-[var(--paper-2)]/90 backdrop-blur">
      <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-4 py-3">
        <Link href="/" className="font-serif text-xl tracking-tight text-[var(--ink)]">
          AcademicCheck <span className="text-[var(--teal)]">AI</span>
        </Link>
        {!compact && (
          <nav className="hidden items-center gap-6 text-sm md:flex" aria-label="Primary">
            {links.map((l) => (
              <Link key={l.href} href={l.href} className="text-[var(--ink)]/80 hover:text-[var(--teal)]">
                {l.label}
              </Link>
            ))}
          </nav>
        )}
        <div className="flex items-center gap-2 text-sm">
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
    </header>
  );
}
