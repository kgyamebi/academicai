"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";

type Assignment = { id: string; title: string; academic_level: string; citation_style: string; created_at?: string };

export default function AssignmentsPage() {
  const [items, setItems] = useState<Assignment[]>([]);
  useEffect(() => {
    api<{ items: Assignment[] }>("/api/assignments").then((d) => setItems(d.items)).catch(() => setItems([]));
  }, []);
  return (
    <main>
      <div className="flex items-center justify-between">
        <h1 className="font-serif text-3xl">Assignments</h1>
        <Link href="/check" className="rounded-md bg-[var(--teal)] px-3 py-2 text-sm text-white">New check</Link>
      </div>
      <ul className="mt-6 space-y-3">
        {items.map((a) => (
          <li key={a.id} className="rounded-lg border border-[var(--rule)] bg-[var(--paper-2)] p-4">
            <Link href={`/app/assignments/${a.id}`} className="font-medium hover:underline">
              {a.title}
            </Link>
            <p className="text-sm text-[var(--ink)]/60">{a.academic_level} · {a.citation_style}</p>
          </li>
        ))}
        {items.length === 0 && <p className="text-sm">No assignments yet.</p>}
      </ul>
    </main>
  );
}
