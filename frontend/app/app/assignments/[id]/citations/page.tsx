"use client";

import Link from "next/link";
import { useParams } from "next/navigation";

export default function CitationsPage() {
  const params = useParams<{ id: string }>();
  return (
    <main>
      <p className="text-sm font-medium tracking-wide text-[var(--teal)]">Citations</p>
      <h1 className="mt-2 font-serif text-3xl">Citations & references</h1>
      <p className="mt-4 max-w-xl text-sm leading-7 text-[var(--ink-muted)]">
        Citation and reference findings appear on the analysis report. Inability to verify a source is not proof that it
        is fabricated. Do not invent replacement references.
      </p>
      <Link
        href={`/app/assignments/${params.id}`}
        className="mt-6 inline-block text-sm font-medium text-[var(--teal)] underline-offset-4 hover:underline"
      >
        Back to assignment
      </Link>
    </main>
  );
}
