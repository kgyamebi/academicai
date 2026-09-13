import Link from "next/link";
import { SiteFooter } from "@/components/SiteFooter";
import { SiteHeader } from "@/components/SiteHeader";
import { apiUrl } from "@/lib/utils";

const docs = [
  ["/help/how-to-check", "How to check an assignment"],
  ["/help/file-types", "Supported file types"],
  ["/help/citation-styles", "Citation styles"],
  ["/help/ai-writing-indicators", "AI-writing indicators"],
  ["/help/rubric-checker", "Rubric checker"],
  ["/help/privacy", "Privacy and data deletion"],
  ["/help/pricing", "Pricing and free launch"],
  ["/terms", "Terms of use"],
  ["/help/academic-integrity", "Academic integrity"],
];

type FaqItem = { question: string; answer: string; category: string };

async function loadFaqs(): Promise<FaqItem[]> {
  try {
    const res = await fetch(`${apiUrl()}/api/public/faqs`, { next: { revalidate: 300 } });
    if (!res.ok) return [];
    const data = await res.json();
    return Array.isArray(data.items) ? data.items : [];
  } catch {
    return [];
  }
}

export default async function HelpPage() {
  const faqs = await loadFaqs();
  const jsonLd =
    faqs.length > 0
      ? {
          "@context": "https://schema.org",
          "@type": "FAQPage",
          mainEntity: faqs.slice(0, 20).map((f) => ({
            "@type": "Question",
            name: f.question,
            acceptedAnswer: { "@type": "Answer", text: f.answer },
          })),
        }
      : null;

  return (
    <>
      <SiteHeader />
      <main id="main-content" tabIndex={-1} className="mx-auto max-w-3xl px-4 py-16">
        <h1 className="font-serif text-4xl">Help centre</h1>
        <ul className="mt-8 space-y-3">
          {docs.map(([href, label]) => (
            <li key={href}>
              <Link className="underline" href={href}>
                {label}
              </Link>
            </li>
          ))}
        </ul>
        {faqs.length > 0 ? (
          <section className="mt-12" aria-labelledby="faq-heading">
            <h2 id="faq-heading" className="font-serif text-2xl">
              Frequently asked questions
            </h2>
            <dl className="mt-6 space-y-4">
              {faqs.map((f) => (
                <div key={f.question}>
                  <dt className="font-medium">{f.question}</dt>
                  <dd className="mt-1 text-sm opacity-90">{f.answer}</dd>
                </div>
              ))}
            </dl>
          </section>
        ) : null}
      </main>
      {jsonLd ? (
        <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }} />
      ) : null}
      <SiteFooter />
    </>
  );
}
