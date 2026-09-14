import Link from "next/link";
import { ButtonLink } from "@/components/ui/Button";

/** Minimal markdown → HTML for SEO guides (headings, lists, paragraphs, links, tables). */
export function renderGuideMarkdown(md: string): string {
  const lines = md.replace(/\r\n/g, "\n").split("\n");
  const html: string[] = [];
  let inUl = false;
  let inTable = false;

  const flushUl = () => {
    if (inUl) {
      html.push("</ul>");
      inUl = false;
    }
  };
  const flushTable = () => {
    if (inTable) {
      html.push("</tbody></table>");
      inTable = false;
    }
  };

  const inline = (text: string) =>
    text
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
      .replace(/\*(.+?)\*/g, "<em>$1</em>")
      .replace(/\[(.+?)\]\((\/[^)]+|https?:\/\/[^)]+)\)/g, '<a href="$2">$1</a>')
      .replace(/`([^`]+)`/g, "<code>$1</code>");

  for (const raw of lines) {
    const line = raw.trimEnd();
    if (!line.trim()) {
      flushUl();
      flushTable();
      continue;
    }
    if (line.startsWith("|") && line.includes("|")) {
      flushUl();
      const cells = line
        .split("|")
        .slice(1, -1)
        .map((c) => c.trim());
      if (cells.every((c) => /^:?-+:?$/.test(c))) continue;
      if (!inTable) {
        html.push('<table class="ac-guide-table"><tbody>');
        inTable = true;
        html.push("<tr>" + cells.map((c) => `<th>${inline(c)}</th>`).join("") + "</tr>");
      } else {
        html.push("<tr>" + cells.map((c) => `<td>${inline(c)}</td>`).join("") + "</tr>");
      }
      continue;
    }
    flushTable();
    if (line.startsWith("### ")) {
      flushUl();
      html.push(`<h3>${inline(line.slice(4))}</h3>`);
      continue;
    }
    if (line.startsWith("## ")) {
      flushUl();
      html.push(`<h2>${inline(line.slice(3))}</h2>`);
      continue;
    }
    if (line.startsWith("# ")) {
      flushUl();
      html.push(`<h2>${inline(line.slice(2))}</h2>`);
      continue;
    }
    if (line.startsWith("- ") || line.startsWith("* ")) {
      if (!inUl) {
        html.push("<ul>");
        inUl = true;
      }
      html.push(`<li>${inline(line.slice(2))}</li>`);
      continue;
    }
    if (/^\d+\.\s/.test(line)) {
      flushUl();
      if (!html.length || !html[html.length - 1].startsWith("<ol")) {
        // simplistic numbered list as paragraphs with numbers kept
      }
      html.push(`<p>${inline(line)}</p>`);
      continue;
    }
    flushUl();
    html.push(`<p>${inline(line)}</p>`);
  }
  flushUl();
  flushTable();
  return html.join("\n");
}

export function ContentCta({
  title = "Check your assignment",
  body = "Get a diagnostic report on question fit, arguments, structure, and citations — not a ghostwritten essay.",
}: {
  title?: string;
  body?: string;
}) {
  return (
    <aside className="mt-14 border-y border-[var(--rule)] bg-[var(--teal-soft)]/40 px-5 py-8">
      <h2 className="font-serif text-2xl text-[var(--ink)]">{title}</h2>
      <p className="mt-2 max-w-2xl text-sm leading-7 text-[var(--ink-muted)]">{body}</p>
      <div className="mt-5 flex flex-wrap gap-3">
        <ButtonLink href="/check" variant="primary">
          Check assignment
        </ButtonLink>
        <ButtonLink href="/sample-report" variant="secondary">
          View sample report
        </ButtonLink>
      </div>
    </aside>
  );
}

export function RelatedLinks({
  heading,
  items,
}: {
  heading: string;
  items: { href: string; label: string }[];
}) {
  if (!items.length) return null;
  return (
    <section className="mt-12" aria-labelledby="related-heading">
      <h2 id="related-heading" className="font-serif text-2xl">
        {heading}
      </h2>
      <ul className="mt-4 space-y-2 text-sm">
        {items.map((item) => (
          <li key={item.href}>
            <Link href={item.href} className="text-[var(--teal)] underline-offset-4 hover:underline">
              {item.label}
            </Link>
          </li>
        ))}
      </ul>
    </section>
  );
}
