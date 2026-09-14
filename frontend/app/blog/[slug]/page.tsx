import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { SiteFooter } from "@/components/SiteFooter";
import { SiteHeader } from "@/components/SiteHeader";
import { ContentCta, RelatedLinks, renderGuideMarkdown } from "@/components/content/GuideBody";
import { allBlogSlugs, getBlogPost } from "@/lib/content/blog";
import { getResource } from "@/lib/content/resources";
import { CATEGORY_LABELS } from "@/lib/content/types";
import { apiUrl, siteUrl } from "@/lib/utils";

type Props = { params: Promise<{ slug: string }> };

async function loadApi(slug: string) {
  try {
    const res = await fetch(`${apiUrl()}/api/public/blog/${slug}`, { next: { revalidate: 300 } });
    if (!res.ok) return null;
    return res.json() as Promise<{
      slug: string;
      title: string;
      excerpt: string;
      body_markdown: string;
      author?: string;
    }>;
  } catch {
    return null;
  }
}

export function generateStaticParams() {
  return allBlogSlugs().map((slug) => ({ slug }));
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { slug } = await params;
  const post = getBlogPost(slug);
  if (post) {
    return {
      title: post.title,
      description: post.description,
      keywords: post.keywords,
      alternates: { canonical: `/blog/${post.slug}` },
      openGraph: { title: post.title, description: post.description, type: "article" },
    };
  }
  const api = await loadApi(slug);
  return api ? { title: api.title, description: api.excerpt } : {};
}

export default async function BlogPostPage({ params }: Props) {
  const { slug } = await params;
  const post = getBlogPost(slug);
  const api = post ? null : await loadApi(slug);
  if (!post && !api) notFound();

  const title = post?.title ?? api!.title;
  const bodyHtml = renderGuideMarkdown(post?.body ?? api!.body_markdown);
  const related =
    post?.relatedResourceSlugs
      ?.map((s) => getResource(s))
      .filter(Boolean)
      .map((g) => ({ href: `/resources/${g!.slug}`, label: g!.title })) ?? [];

  const jsonLd = post
    ? {
        "@context": "https://schema.org",
        "@type": "BlogPosting",
        headline: post.title,
        description: post.description,
        datePublished: post.published,
        author: { "@type": "Person", name: post.author },
        mainEntityOfPage: `${siteUrl()}/blog/${post.slug}`,
      }
    : null;

  return (
    <>
      <SiteHeader />
      <main id="main-content" tabIndex={-1} className="mx-auto max-w-3xl px-4 py-14">
        <nav aria-label="Breadcrumb" className="text-sm text-[var(--ink-muted)]">
          <Link href="/blog" className="hover:text-[var(--ink)]">
            Blog
          </Link>
          <span aria-hidden="true"> / </span>
          <span>{post ? CATEGORY_LABELS[post.category] : "Guide"}</span>
        </nav>
        <h1 className="mt-6 font-serif text-4xl leading-tight md:text-[2.6rem]">{title}</h1>
        {post ? (
          <p className="mt-4 text-sm text-[var(--ink-muted)]">
            {post.author} · {post.published} · {post.readingMinutes} min read
          </p>
        ) : null}
        <article className="ac-guide mt-10" dangerouslySetInnerHTML={{ __html: bodyHtml }} />
        <RelatedLinks heading="Related resources" items={related} />
        <RelatedLinks
          heading="More"
          items={[
            { href: "/resources", label: "Resources centre" },
            { href: "/blog", label: "All writing guides" },
            { href: "/sample-report", label: "Sample report" },
          ]}
        />
        <ContentCta />
      </main>
      {jsonLd ? (
        <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }} />
      ) : null}
      <SiteFooter />
    </>
  );
}
