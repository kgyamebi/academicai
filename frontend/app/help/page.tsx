import Link from "next/link";
import { SiteFooter } from "@/components/SiteFooter";
import { SiteHeader } from "@/components/SiteHeader";

const docs = [
  ["/help/how-to-check", "How to check an assignment"],
  ["/help/file-types", "Supported file types"],
  ["/help/citation-styles", "Citation styles"],
  ["/help/ai-writing-indicators", "AI-writing indicators"],
  ["/help/rubric-checker", "Rubric checker"],
  ["/help/privacy", "Privacy and data deletion"],
  ["/help/pricing", "Pricing and credits"],
  ["/help/academic-integrity", "Academic integrity"],
];

export default function HelpPage() {
  return (
    <>
      <SiteHeader />
      <main className="mx-auto max-w-3xl px-4 py-16">
        <h1 className="font-serif text-4xl">Help centre</h1>
        <ul className="mt-8 space-y-3">
          {docs.map(([href, label]) => (
            <li key={href}><Link className="underline" href={href}>{label}</Link></li>
          ))}
        </ul>
      </main>
      <SiteFooter />
    </>
  );
}
