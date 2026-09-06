import Link from "next/link";
import { SiteFooter } from "@/components/SiteFooter";
import { SiteHeader } from "@/components/SiteHeader";
import { apiUrl } from "@/lib/utils";

export default async function BlogIndex() {
  const res = await fetch(`${apiUrl()}/api/public/blog`, { next: { revalidate: 300 } });
  const data = res.ok ? await res.json() : { items: [] };
  return (
    <>
      <SiteHeader />
      <main className="mx-auto max-w-3xl px-4 py-16">
        <h1 className="font-serif text-4xl">Writing guides</h1>
        <ul className="mt-8 space-y-5">
          {data.items.map((p: { slug: string; title: string; excerpt: string }) => (
            <li key={p.slug}>
              <Link href={`/blog/${p.slug}`} className="font-serif text-2xl hover:underline">{p.title}</Link>
              <p className="text-sm text-[var(--ink-muted)]">{p.excerpt}</p>
            </li>
          ))}
        </ul>
      </main>
      <SiteFooter />
    </>
  );
}
