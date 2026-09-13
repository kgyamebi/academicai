"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/Button";
import { EmptyState, SkeletonBlock } from "@/components/ui/EmptyState";

export default function VersionsPage() {
  const params = useParams<{ id: string }>();
  const [versions, setVersions] = useState<{ id: string; name: string; version_number: number }[]>([]);
  const [compare, setCompare] = useState<Record<string, unknown> | null>(null);
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api<{ versions: { id: string; name: string; version_number: number }[] }>(`/api/assignments/${params.id}`)
      .then((d) => setVersions(d.versions || []))
      .finally(() => setLoading(false));
  }, [params.id]);

  async function runCompare() {
    if (versions.length < 2) return;
    setBusy(true);
    try {
      const data = await api<Record<string, unknown>>("/api/analysis/compare", {
        method: "POST",
        body: JSON.stringify({
          assignment_id: params.id,
          version_a_id: versions[0].id,
          version_b_id: versions[versions.length - 1].id,
        }),
      });
      setCompare(data);
    } finally {
      setBusy(false);
    }
  }

  return (
    <main>
      <p className="text-sm font-medium tracking-wide text-[var(--teal)]">Versions</p>
      <h1 className="mt-2 font-serif text-3xl">Compare drafts</h1>
      <p className="mt-3 max-w-xl text-sm leading-7 text-[var(--ink-muted)]">
        Track how your writing improves across submissions. Compare uses your earliest and latest saved versions.
      </p>
      {loading ? (
        <div className="mt-8">
          <SkeletonBlock lines={4} />
        </div>
      ) : versions.length === 0 ? (
        <EmptyState
          className="mt-8"
          title="No versions yet"
          body="Run a check on this assignment to create your first draft version."
          actionHref={`/app/assignments/${params.id}/check`}
          actionLabel="Check this draft"
        />
      ) : (
        <>
          <ul className="mt-8 space-y-2">
            {versions.map((v) => (
              <li key={v.id} className="ac-surface px-4 py-3 text-sm">
                <span className="font-medium">v{v.version_number}</span> · {v.name}
              </li>
            ))}
          </ul>
          <Button type="button" busy={busy} onClick={runCompare} className="mt-6" disabled={versions.length < 2}>
            Compare earliest and latest
          </Button>
          {compare ? (
            <pre className="mt-6 overflow-auto rounded-[var(--radius-md)] border border-[var(--rule)] bg-[var(--paper-2)] p-4 text-sm">
              {JSON.stringify(compare, null, 2)}
            </pre>
          ) : null}
        </>
      )}
    </main>
  );
}
