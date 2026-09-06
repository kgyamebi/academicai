"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { clearTokens } from "@/lib/api";

const nav = [
  { href: "/app/dashboard", label: "Dashboard" },
  { href: "/app/assignments", label: "Assignments" },
  { href: "/check", label: "New check" },
  { href: "/app/coach", label: "Coach" },
  { href: "/app/billing", label: "Billing" },
  { href: "/app/settings", label: "Settings" },
];

export default function AppLayout({ children }: { children: React.ReactNode }) {
  const path = usePathname();
  return (
    <div className="min-h-screen md:grid md:grid-cols-[220px_1fr]">
      <aside className="border-b border-[var(--rule)] bg-[var(--paper-2)] md:border-b-0 md:border-r">
        <div className="px-4 py-4 font-serif text-lg">
          <Link href="/">AcademicCheck AI</Link>
        </div>
        <nav className="flex gap-2 overflow-x-auto px-3 pb-3 md:flex-col" aria-label="App">
          {nav.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className={`rounded-md px-3 py-2 text-sm ${path === item.href ? "bg-[var(--teal)] text-white" : "hover:bg-black/5"}`}
            >
              {item.label}
            </Link>
          ))}
          <button
            className="rounded-md px-3 py-2 text-left text-sm hover:bg-black/5"
            onClick={() => {
              clearTokens();
              window.location.href = "/";
            }}
          >
            Sign out
          </button>
        </nav>
      </aside>
      <div className="px-4 py-6 md:px-8">{children}</div>
    </div>
  );
}
