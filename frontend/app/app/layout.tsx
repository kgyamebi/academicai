"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Suspense } from "react";
import { useAuth } from "@/components/AuthProvider";
import { EmailVerifyBanner } from "@/components/EmailVerifyBanner";
import { SignupConversionBeacon } from "@/components/SignupConversionBeacon";

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

export default function AppLayout({ children }: { children: React.ReactNode }) {
  const path = usePathname();
  const { user, signedIn, needsVerify, signOut } = useAuth();

  return (
    <div className="min-h-screen md:grid md:grid-cols-[240px_1fr]">
      <aside className="hidden border-r border-[var(--rule)] bg-[var(--paper-2)] md:block">
        <div className="px-5 py-5 font-serif text-lg">
          <Link href={signedIn ? "/app/dashboard" : "/"}>
            AcademicCheck <span className="text-[var(--teal)]">AI</span>
          </Link>
        </div>
        {signedIn && user?.email ? (
          <div className="mx-3 mb-3 rounded-[var(--radius-sm)] border border-[var(--rule)] bg-[var(--paper)] px-3 py-2">
            <p className="truncate text-xs font-medium text-[var(--ink)]" title={user.email}>
              {user.full_name || user.email}
            </p>
            <p className="mt-0.5 text-[11px] text-[var(--ink-muted)]">
              {needsVerify ? "Signed in · verify email" : "Signed in"}
            </p>
          </div>
        ) : null}
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
          {signedIn ? (
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
          ) : (
            <Link
              href="/login"
              className="ac-hit justify-start rounded-[var(--radius-sm)] px-3 text-sm text-[var(--ink-muted)] hover:bg-black/[0.04] hover:text-[var(--ink)]"
            >
              Sign in
            </Link>
          )}
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
          <Suspense fallback={null}>
            <SignupConversionBeacon />
          </Suspense>
          {needsVerify && user ? (
            <EmailVerifyBanner email={user.pending_email || user.email || ""} />
          ) : null}
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
