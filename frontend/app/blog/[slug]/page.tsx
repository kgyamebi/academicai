import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { SiteFooter } from "@/components/SiteFooter";
import { SiteHeader } from "@/components/SiteHeader";
import { apiUrl } from "@/lib/utils";

async function load(slug: string) {
  const res = await fetch(`${apiUrl()}/api/public/blog/${slug}`, { next: { revalidate: 300 } });
  if (!res.ok) return null;
  return res.json();
}

export async function generateMetadata({ params }: { params: Promise<{ slug: string }> }): Promise<Metadata> {
  const { slug } = await params;
  const post = await load(slug);
  return post ? { title: post.title, description: post.excerpt } : {};
}

export default async function BlogPost({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const post = await load(slug);
  if (!post) notFound();
  return (
    <>
      <SiteHeader />
      <main className="prose-academic mx-auto max-w-3xl px-4 py-16">
        <article className="whitespace-pre-wrap leading-7">{post.body_markdown}</article>
      </main>
      <SiteFooter />
    </>
  );
}
