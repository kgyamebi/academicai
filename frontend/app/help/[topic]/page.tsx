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
    body: "Free, Student ($1.99), Pro Student ($3.99), Power ($7.99), plus institution and one-time credits. Credit costs are configurable. Payments are verified server-side via signed webhooks.",
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
      <main className="mx-auto max-w-3xl px-4 py-16">
        <h1 className="font-serif text-4xl">{page.title}</h1>
        <p className="mt-6 leading-7">{page.body}</p>
      </main>
      <SiteFooter />
    </>
  );
}
