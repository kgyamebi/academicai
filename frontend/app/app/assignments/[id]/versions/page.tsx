"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { api } from "@/lib/api";

export default function VersionsPage() {
  const params = useParams<{ id: string }>();
  const [versions, setVersions] = useState<{ id: string; name: string; version_number: number }[]>([]);
  const [compare, setCompare] = useState<Record<string, unknown> | null>(null);
  useEffect(() => {
    api<{ versions: { id: string; name: string; version_number: number }[] }>(`/api/assignments/${params.id}`).then((d) => setVersions(d.versions));
  }, [params.id]);
  async function runCompare() {
    if (versions.length < 2) return;
    const data = await api<Record<string, unknown>>("/api/analysis/compare", {
      method: "POST",
      body: JSON.stringify({
        assignment_id: params.id,
        version_a_id: versions[0].id,
        version_b_id: versions[versions.length - 1].id,
      }),
    });
    setCompare(data);
  }
  return (
    <main>
      <h1 className="font-serif text-3xl">Versions</h1>
      <ul className="mt-4 space-y-2">
        {versions.map((v) => (
          <li key={v.id} className="rounded-md border border-[var(--rule)] p-3">{v.name}</li>
        ))}
      </ul>
      <button type="button" onClick={runCompare} className="mt-6 rounded-md bg-[var(--teal)] px-4 py-2 text-white">Compare drafts</button>
      {compare && (
        <pre className="mt-6 overflow-auto rounded-md bg-[var(--paper-2)] p-4 text-sm">{JSON.stringify(compare, null, 2)}</pre>
      )}
    </main>
  );
}
