import Link from "next/link";
import { messages } from "@/lib/i18n";

export function SiteFooter() {
  return (
    <footer className="mt-24 border-t border-[var(--rule)] bg-[var(--paper-2)]">
      <div className="mx-auto grid max-w-6xl gap-10 px-4 py-14 md:grid-cols-4">
        <div>
          <p className="font-serif text-lg">
            AcademicCheck <span className="text-[var(--teal)]">AI</span>
          </p>
          <p className="mt-3 text-sm leading-7 text-[var(--ink-muted)]">{messages.tagline}</p>
        </div>
        <div>
          <p className="text-sm font-semibold text-[var(--ink)]">Product</p>
          <nav aria-label="Product">
            <ul className="mt-3 space-y-2.5 text-sm text-[var(--ink-muted)]">
              <li>
                <Link className="hover:text-[var(--ink)]" href="/assignment-checker">
                  Assignment checker
                </Link>
              </li>
              <li>
                <Link className="hover:text-[var(--ink)]" href="/thesis-checker">
                  Thesis checker
                </Link>
              </li>
              <li>
                <Link className="hover:text-[var(--ink)]" href="/citation-checker">
                  Citation checker
                </Link>
              </li>
              <li>
                <Link className="hover:text-[var(--ink)]" href="/sample-report">
                  Sample report
                </Link>
              </li>
              <li>
                <Link className="hover:text-[var(--ink)]" href="/pricing">
                  Pricing
                </Link>
              </li>
            </ul>
          </nav>
        </div>
        <div>
          <p className="text-sm font-semibold text-[var(--ink)]">Learn</p>
          <nav aria-label="Learn">
            <ul className="mt-3 space-y-2.5 text-sm text-[var(--ink-muted)]">
              <li>
                <Link className="hover:text-[var(--ink)]" href="/resources">
                  Resources centre
                </Link>
              </li>
              <li>
                <Link className="hover:text-[var(--ink)]" href="/blog">
                  Writing guides
                </Link>
              </li>
              <li>
                <Link className="hover:text-[var(--ink)]" href="/help">
                  Help centre
                </Link>
              </li>
              <li>
                <Link className="hover:text-[var(--ink)]" href="/help/academic-integrity">
                  Academic integrity
                </Link>
              </li>
              <li>
                <Link className="hover:text-[var(--ink)]" href="/help/privacy">
                  Privacy
                </Link>
              </li>
            </ul>
          </nav>
        </div>
        <div>
          <p className="text-sm font-semibold text-[var(--ink)]">Trust</p>
          <nav aria-label="Trust">
            <ul className="mt-3 space-y-2.5 text-sm text-[var(--ink-muted)]">
              <li>
                <Link className="hover:text-[var(--ink)]" href="/about">
                  About
                </Link>
              </li>
              <li>
                <Link className="hover:text-[var(--ink)]" href="/contact">
                  Contact
                </Link>
              </li>
              <li>
                <Link className="hover:text-[var(--ink)]" href="/security">
                  Security
                </Link>
              </li>
              <li>
                <Link className="hover:text-[var(--ink)]" href="/terms">
                  Terms
                </Link>
              </li>
              <li>
                <Link className="hover:text-[var(--ink)]" href="/help/privacy">
                  Privacy
                </Link>
              </li>
              <li>
                <Link className="hover:text-[var(--ink)]" href="/help/academic-integrity">
                  Academic integrity
                </Link>
              </li>
            </ul>
          </nav>
          <p className="mt-4 text-sm leading-7 text-[var(--ink-muted)]">{messages.disclaimer}</p>
        </div>
      </div>
    </footer>
  );
}
