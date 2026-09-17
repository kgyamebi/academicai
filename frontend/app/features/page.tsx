import type { Metadata } from "next";
import { SiteFooter } from "@/components/SiteFooter";
import { SiteHeader } from "@/components/SiteHeader";

export const metadata: Metadata = {
  title: "Features — what AcademicCheck AI analyses",
  description:
    "Assignment relevance, thesis, argument, evidence, structure, academic writing, citations, and fix-first priorities — before you submit.",
  alternates: { canonical: "/features" },
};

const features = [
  ["Assignment relevance", "Did the draft actually answer the question?"],
  ["Thesis checker", "Is the claim specific, arguable, and supported?"],
  ["Argument & evidence", "Claims, support, counterargument, and missing analysis."],
  ["Structure map", "Introduction, body, counterargument, conclusion, references."],
  ["Academic writing", "Clarity and formality — not artificially complicated vocabulary."],
  ["Citations", "APA 7, MLA 9, Harvard, Chicago, IEEE, with mismatch warnings."],
  ["Priority actions", "Fix the highest-impact issues first."],
  ["Draft comparison", "See whether a revision actually improved the work."],
];

export default function FeaturesPage() {
  return (
    <>
      <SiteHeader />
      <main id="main-content" tabIndex={-1} className="mx-auto max-w-5xl px-4 py-16">
        <h1 className="font-serif text-4xl">What AcademicCheck AI analyses</h1>
        <div className="mt-10 grid gap-4 md:grid-cols-2">
          {features.map(([t, d]) => (
            <article key={t} className="rounded-xl border border-[var(--rule)] bg-[var(--paper-2)] p-5">
              <h2 className="font-serif text-xl">{t}</h2>
              <p className="mt-2 text-sm leading-6">{d}</p>
            </article>
          ))}
        </div>
      </main>
      <SiteFooter />
    </>
  );
}
