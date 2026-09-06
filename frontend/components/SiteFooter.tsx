import Link from "next/link";
import { messages } from "@/lib/i18n";

export function SiteFooter() {
  return (
    <footer className="mt-20 border-t border-[var(--rule)] bg-[var(--paper-2)]">
      <div className="mx-auto grid max-w-6xl gap-8 px-4 py-12 md:grid-cols-4">
        <div>
          <p className="font-serif text-lg">AcademicCheck AI</p>
          <p className="mt-2 text-sm leading-6 text-[var(--ink)]/70">{messages.tagline}</p>
        </div>
        <div>
          <p className="text-sm font-semibold">Product</p>
          <ul className="mt-3 space-y-2 text-sm">
            <li><Link href="/assignment-checker">Assignment checker</Link></li>
            <li><Link href="/thesis-checker">Thesis checker</Link></li>
            <li><Link href="/citation-checker">Citation checker</Link></li>
            <li><Link href="/pricing">Pricing</Link></li>
          </ul>
        </div>
        <div>
          <p className="text-sm font-semibold">Learn</p>
          <ul className="mt-3 space-y-2 text-sm">
            <li><Link href="/blog">Writing guides</Link></li>
            <li><Link href="/help">Help centre</Link></li>
            <li><Link href="/help/academic-integrity">Academic integrity</Link></li>
            <li><Link href="/help/privacy">Privacy</Link></li>
          </ul>
        </div>
        <div>
          <p className="text-sm font-semibold">Trust</p>
          <p className="mt-3 text-sm leading-6 text-[var(--ink)]/70">{messages.disclaimer}</p>
        </div>
      </div>
    </footer>
  );
}
