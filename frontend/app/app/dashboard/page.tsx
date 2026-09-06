"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";

type Dash = {
  assignments: number;
  average_score: number | null;
  checks_used: number;
  checks_remaining: number;
  plan: string;
  improvement_trend: number[];
  recent_reports: { id: string; score: number; summary: string; created_at: string }[];
  recent_documents: { id: string; filename: string; word_count: number }[];
};

export default function DashboardPage() {
  const [data, setData] = useState<Dash | null>(null);
  const [error, setError] = useState("");
  useEffect(() => {
    api<Dash>("/api/dashboard")
      .then(setData)
      .catch((e) => setError(e.message));
  }, []);
  if (error) {
    return (
      <p>
        {error} <Link href="/login" className="underline">Sign in</Link>
      </p>
    );
  }
  if (!data) return <p>Loading dashboard…</p>;
  return (
    <main>
      <h1 className="font-serif text-3xl">Dashboard</h1>
      <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Stat label="Assignments" value={String(data.assignments)} />
        <Stat label="Average score" value={data.average_score != null ? `${data.average_score}` : "—"} />
        <Stat label="Checks remaining" value={String(data.checks_remaining)} />
        <Stat label="Plan" value={data.plan} />
      </div>
      <section className="mt-10">
        <h2 className="font-serif text-2xl">Recent reports</h2>
        <ul className="mt-4 space-y-3">
          {data.recent_reports.map((r) => (
            <li key={r.id} className="rounded-lg border border-[var(--rule)] bg-[var(--paper-2)] p-4">
              <p className="font-medium">{r.score}/100</p>
              <p className="text-sm text-[var(--ink)]/70">{r.summary}</p>
              <Link className="mt-2 inline-block text-sm underline" href={`/app/assignments`}>
                Open workspace
              </Link>
            </li>
          ))}
          {data.recent_reports.length === 0 && <p className="text-sm">No reports yet. Start with a check.</p>}
        </ul>
      </section>
    </main>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-[var(--rule)] bg-[var(--paper-2)] p-4">
      <p className="text-xs uppercase tracking-wide text-[var(--ink)]/60">{label}</p>
      <p className="mt-2 font-serif text-2xl">{value}</p>
    </div>
  );
}
