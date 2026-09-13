import { notFound } from "next/navigation";
import { SiteFooter } from "@/components/SiteFooter";
import { SiteHeader } from "@/components/SiteHeader";

const content: Record<string, { title: string; body: string }> = {
  "how-to-check": {
    title: "How to check an assignment",
    body: "Paste the assignment question, choose academic level and citation style, then paste or upload your draft. Analysis runs as a job. Progress reflects real stages: extracting, structure, arguments, citations, report.",
  },
  "file-types": {
    title: "Supported file types",
    body: "MVP: DOCX, PDF, TXT, Markdown. PPTX, ODT and RTF are reserved in the architecture. Uploads are checked by MIME type, file signature and size — not the extension alone.",
  },
  "citation-styles": {
    title: "Citation styles",
    body: "Supported now: APA 7, MLA 9, Chicago, Harvard, IEEE. Prepared for Vancouver, AMA, OSCOLA and Turabian. A missing match is not proof a source is fake.",
  },
  "ai-writing-indicators": {
    title: "AI-writing indicators",
    body: "This optional module is qualitative (low / moderate / high). Detection is uncertain. Never treat it as proof that a student used AI, and never as a misconduct finding.",
  },
  "rubric-checker": {
    title: "Rubric checker",
    body: "Paste or enter criteria with weights. The result is an AI-assisted rubric assessment — not an official grade, and not a claim about what a lecturer will award.",
  },
  privacy: {
    title: "Privacy and data deletion",
    body: "Assignments can be sensitive. Guest files are retained briefly (default 24 hours). Account documents stay until you delete them or a retention policy applies. We do not sell documents or use them for training by default. Account deletion disables login and deletes document text; legally required financial records may be retained.",
  },
  pricing: {
    title: "Pricing and credits",
    body: "Public free launch: paid subscriptions and checkout are intentionally disabled. You can use the product under fair-use limits with no payment flow. Future paid tiers (when re-enabled) will unlock higher monthly limits; charges will only ever happen after verified server-side payment confirmation — never from the browser alone.",
  },
  terms: {
    title: "Terms of use (summary)",
    body: "AcademicCheck AI is a diagnostic study aid. It does not guarantee grades, write submissions for you, or invent sources. You remain responsible for academic integrity. Full terms live at /terms.",
  },
  "academic-integrity": {
    title: "Academic integrity",
    body: "AcademicCheck AI helps you understand feedback and improve your own writing. It does not write an assignment for submission, invent sources, fabricate quotations or statistics, or guarantee a grade. Follow your institution’s policies.",
  },
};

export default async function HelpTopic({ params }: { params: Promise<{ topic: string }> }) {
  const { topic } = await params;
  const page = content[topic];
  if (!page) notFound();
  return (
    <>
      <SiteHeader />
      <main id="main-content" tabIndex={-1} className="mx-auto max-w-3xl px-4 py-16">
        <h1 className="font-serif text-4xl">{page.title}</h1>
        <p className="mt-6 leading-7">{page.body}</p>
      </main>
      <SiteFooter />
    </>
  );
}
