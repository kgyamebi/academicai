import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Check my assignment",
  description:
    "Paste your assignment question and draft for a free diagnostic check of thesis, argument, evidence, structure, and citations.",
  alternates: { canonical: "/check" },
  openGraph: {
    title: "Check my assignment | AcademicCheck AI",
    description:
      "Paste your assignment question and draft for a free diagnostic check before you submit.",
    url: "/check",
  },
};

export default function CheckLayout({ children }: { children: React.ReactNode }) {
  return children;
}
