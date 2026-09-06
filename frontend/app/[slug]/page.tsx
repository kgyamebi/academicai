import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { SiteFooter } from "@/components/SiteFooter";
import { SiteHeader } from "@/components/SiteHeader";
import { apiUrl, siteUrl } from "@/lib/utils";

async function loadPage(slug: string) {
  const res = await fetch(`${apiUrl()}/api/public/seo/${slug}`, { next: { revalidate: 300 } });
  if (!res.ok) return null;
  return res.json() as Promise<{ title: string; meta_description: string; heading: string; body_markdown: string; canonical_path: string }>;
}

export async function generateMetadata({ params }: { params: Promise<{ slug: string }> }): Promise<Metadata> {
  const { slug } = await params;
  const page = await loadPage(slug);
  if (!page) return {};
  return {
    title: page.title,
    description: page.meta_description,
    alternates: { canonical: `${siteUrl()}${page.canonical_path}` },
    openGraph: { title: page.heading, description: page.meta_description },
  };
}

export default async function SeoPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const reserved = new Set(["app", "check", "login", "register", "pricing", "features", "blog", "help", "shared", "verify", "forgot-password", "reset-password"]);
  if (reserved.has(slug)) notFound();
  const page = await loadPage(slug);
  if (!page) notFound();
  return (
    <>
      <SiteHeader />
      <main className="prose-academic mx-auto max-w-3xl px-4 py-16">
        <article className="whitespace-pre-wrap leading-7">{page.body_markdown}</article>
        <p className="mt-10 text-sm text-[var(--ink-muted)]">
          AI-assisted feedback is not an official grade. Always follow your institution’s academic-integrity policies.
        </p>
      </main>
      <SiteFooter />
    </>
  );
}
