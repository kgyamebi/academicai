"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { api } from "@/lib/api";
import { Button, ButtonLink } from "@/components/ui/Button";
import { EmptyState, SkeletonBlock } from "@/components/ui/EmptyState";
import { cn } from "@/lib/utils";

type Version = { id: string; name: string; version_number: number };

type CompareSummary = {
  draft_1: number;
  draft_2: number;
  improved: string[];
  needs_attention: string[];
  categories: Record<string, { draft_1?: number | null; draft_2?: number | null }>;
};

function categoryTitle(key: string) {
  return key.replaceAll("_", " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

export default function VersionsPage() {
  const params = useParams<{ id: string }>();
  const [versions, setVersions] = useState<Version[]>([]);
  const [compare, setCompare] = useState<CompareSummary | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api<{ versions: Version[] }>(`/api/assignments/${params.id}`)
      .then((d) => setVersions(d.versions || []))
      .finally(() => setLoading(false));
  }, [params.id]);

  async function runCompare() {
    if (versions.length < 2) return;
    setBusy(true);
    setError("");
    try {
      const data = await api<CompareSummary>("/api/analysis/compare", {
        method: "POST",
        body: JSON.stringify({
          assignment_id: params.id,
          version_a_id: versions[0].id,
          version_b_id: versions[versions.length - 1].id,
        }),
      });
      setCompare(data);
    } catch (e) {
      setCompare(null);
      setError(e instanceof Error ? e.message : "Could not compare drafts.");
    } finally {
      setBusy(false);
    }
  }

  const delta =
    compare != null ? Math.round(compare.draft_2 - compare.draft_1) : null;

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
            {versions.map((v, i) => (
              <li key={v.id} className="ac-surface flex items-center justify-between gap-3 px-4 py-3 text-sm">
                <span>
                  <span className="font-medium">Draft {v.version_number}</span>
                  <span className="text-[var(--ink-muted)]"> · {v.name}</span>
                </span>
                {i === 0 ? (
                  <span className="text-xs text-[var(--ink-muted)]">Earliest</span>
                ) : i === versions.length - 1 ? (
                  <span className="text-xs font-medium text-[var(--teal)]">Latest</span>
                ) : null}
              </li>
            ))}
          </ul>

          <div className="mt-6 flex flex-wrap items-center gap-3">
            <Button type="button" busy={busy} onClick={runCompare} disabled={versions.length < 2}>
              Compare earliest and latest
            </Button>
            <ButtonLink href={`/app/assignments/${params.id}/check`} variant="secondary">
              Re-score a revised draft
            </ButtonLink>
          </div>
          {versions.length < 2 ? (
            <p className="mt-3 text-sm text-[var(--ink-muted)]">
              Save or analyse at least two drafts to unlock a comparison.
            </p>
          ) : null}
          {error ? (
            <p role="alert" className="mt-3 text-sm text-[var(--crimson)]">
              {error}
            </p>
          ) : null}

          {compare ? (
            <section className="ac-surface mt-8 space-y-6 p-5 md:p-6" aria-label="What improved">
              <div>
                <h2 className="font-serif text-2xl">What improved</h2>
                <p className="mt-1 text-sm text-[var(--ink-muted)]">
                  Fresh evaluation vs your earlier draft — same assignment, two scores.
                </p>
              </div>

              <div className="grid gap-3 sm:grid-cols-3">
                <div className="rounded-[var(--radius-sm)] border border-[var(--rule)] px-3 py-3">
                  <p className="text-xs uppercase tracking-wide text-[var(--ink-muted)]">Earlier draft</p>
                  <p className="mt-1 font-serif text-2xl tabular-nums">{compare.draft_1}</p>
                </div>
                <div className="rounded-[var(--radius-sm)] border border-[var(--rule)] px-3 py-3">
                  <p className="text-xs uppercase tracking-wide text-[var(--ink-muted)]">Latest draft</p>
                  <p className="mt-1 font-serif text-2xl tabular-nums">{compare.draft_2}</p>
                </div>
                <div className="rounded-[var(--radius-sm)] border border-[var(--rule)] px-3 py-3">
                  <p className="text-xs uppercase tracking-wide text-[var(--ink-muted)]">Change</p>
                  <p
                    className={cn(
                      "mt-1 font-serif text-2xl tabular-nums",
                      delta == null
                        ? "text-[var(--ink-muted)]"
                        : delta >= 0
                          ? "text-[var(--forest)]"
                          : "text-[var(--crimson)]",
                    )}
                  >
                    {delta == null ? "—" : `${delta >= 0 ? "+" : ""}${delta}`}
                  </p>
                </div>
              </div>

              {compare.improved.length ? (
                <div>
                  <p className="text-xs font-semibold uppercase tracking-wide text-[var(--forest)]">Improved</p>
                  <ul className="mt-2 space-y-1.5 text-sm text-[var(--ink)]">
                    {compare.improved.map((item) => (
                      <li key={item}>· {item}</li>
                    ))}
                  </ul>
                </div>
              ) : (
                <p className="text-sm text-[var(--ink-muted)]">No clear category gains yet — keep revising the Fix-First items.</p>
              )}

              {compare.needs_attention.length ? (
                <div>
                  <p className="text-xs font-semibold uppercase tracking-wide text-[var(--amber)]">Still needs work</p>
                  <ul className="mt-2 space-y-1.5 text-sm text-[var(--ink)]">
                    {compare.needs_attention.map((item) => (
                      <li key={item}>· {item}</li>
                    ))}
                  </ul>
                </div>
              ) : null}

              <div>
                <p className="text-xs font-semibold uppercase tracking-wide text-[var(--ink-muted)]">By category</p>
                <ul className="mt-3 space-y-2">
                  {Object.entries(compare.categories).map(([key, row]) => {
                    const a = row.draft_1 ?? 0;
                    const b = row.draft_2 ?? 0;
                    const d = b - a;
                    return (
                      <li key={key} className="flex items-center justify-between gap-3 text-sm">
                        <span>{categoryTitle(key)}</span>
                        <span className="tabular-nums text-[var(--ink-muted)]">
                          {a} → {b}{" "}
                          <span className={d >= 0 ? "text-[var(--forest)]" : "text-[var(--crimson)]"}>
                            ({d >= 0 ? "+" : ""}
                            {d})
                          </span>
                        </span>
                      </li>
                    );
                  })}
                </ul>
              </div>

              <p className="text-sm">
                <Link
                  href={`/app/assignments/${params.id}/check`}
                  className="font-medium text-[var(--teal)] underline-offset-4 hover:underline"
                >
                  Upload another revision and re-score
                </Link>
              </p>
            </section>
          ) : null}
        </>
      )}
    </main>
  );
}
