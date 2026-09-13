"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { EmailVerifyBanner } from "@/components/EmailVerifyBanner";
import { api, signOut } from "@/lib/api";

const sideNav = [
  { href: "/app/dashboard", label: "Dashboard" },
  { href: "/app/assignments", label: "Progress" },
  { href: "/check", label: "New check" },
  { href: "/app/coach", label: "Mentor" },
  { href: "/app/settings", label: "Settings" },
];

const bottomNav = [
  { href: "/app/dashboard", label: "Home" },
  { href: "/app/assignments", label: "Progress" },
  { href: "/check", label: "Check" },
  { href: "/app/coach", label: "Mentor" },
  { href: "/app/settings", label: "Account" },
];

function active(path: string, href: string) {
  return path === href || path.startsWith(`${href}/`);
}

type Me = {
  email?: string | null;
  is_guest?: boolean;
  email_verified?: boolean;
  pending_email?: string | null;
};

export default function AppLayout({ children }: { children: React.ReactNode }) {
  const path = usePathname();
  const [me, setMe] = useState<Me | null>(null);

  useEffect(() => {
    api<Me>("/api/auth/me")
      .then(setMe)
      .catch(() => setMe(null));
  }, [path]);

  const showBanner =
    me && !me.is_guest && me.email && (!me.email_verified || Boolean(me.pending_email));

  return (
    <div className="min-h-screen md:grid md:grid-cols-[240px_1fr]">
      <aside className="hidden border-r border-[var(--rule)] bg-[var(--paper-2)] md:block">
        <div className="px-5 py-5 font-serif text-lg">
          <Link href="/">
            AcademicCheck <span className="text-[var(--teal)]">AI</span>
          </Link>
        </div>
        <nav className="flex flex-col gap-1 px-3 pb-3" aria-label="App">
          {sideNav.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              aria-current={active(path, item.href) ? "page" : undefined}
              className={`ac-hit justify-start rounded-[var(--radius-sm)] px-3 text-sm transition-colors ${
                active(path, item.href)
                  ? "bg-[var(--teal)] text-white"
                  : "text-[var(--ink-muted)] hover:bg-black/[0.04] hover:text-[var(--ink)]"
              }`}
            >
              {item.label}
            </Link>
          ))}
          <button
            type="button"
            className="ac-hit justify-start rounded-[var(--radius-sm)] px-3 text-left text-sm text-[var(--ink-muted)] hover:bg-black/[0.04] hover:text-[var(--ink)]"
            onClick={async () => {
              await signOut();
              window.location.href = "/";
            }}
          >
            Sign out
          </button>
        </nav>
      </aside>

      <div className="flex min-h-screen flex-col">
        <div className="flex items-center justify-between border-b border-[var(--rule)] bg-[var(--paper-2)] px-4 py-3 md:hidden">
          <Link href="/app/dashboard" className="font-serif text-lg">
            AcademicCheck <span className="text-[var(--teal)]">AI</span>
          </Link>
          <Link href="/app/settings" className="text-sm text-[var(--ink-muted)]">
            Settings
          </Link>
        </div>

        <div id="main-content" tabIndex={-1} className="flex-1 px-4 py-6 pb-28 md:px-10 md:py-8 md:pb-8">
          {showBanner ? <EmailVerifyBanner email={me.pending_email || me.email || ""} /> : null}
          {children}
        </div>

        <nav
          className="fixed inset-x-0 bottom-0 z-40 border-t border-[var(--rule)] bg-[var(--paper-2)]/95 backdrop-blur md:hidden"
          aria-label="Primary mobile"
        >
          <ul className="mx-auto grid max-w-lg grid-cols-5 gap-1 px-2 pb-[max(0.5rem,env(safe-area-inset-bottom))] pt-2">
            {bottomNav.map((item) => {
              const isActive = active(path, item.href);
              return (
                <li key={item.href}>
                  <Link
                    href={item.href}
                    aria-current={isActive ? "page" : undefined}
                    className={`ac-hit flex w-full flex-col gap-0.5 rounded-[var(--radius-sm)] px-1 text-[11px] font-medium ${
                      isActive ? "text-[var(--teal)]" : "text-[var(--ink-muted)]"
                    }`}
                  >
                    <span
                      className={`h-1 w-1 rounded-full ${isActive ? "bg-[var(--teal)]" : "bg-transparent"}`}
                      aria-hidden
                    />
                    {item.label}
                  </Link>
                </li>
              );
            })}
          </ul>
        </nav>
      </div>
    </div>
  );
}
