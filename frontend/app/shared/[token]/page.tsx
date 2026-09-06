"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { api } from "@/lib/api";
import { ScoreRing } from "@/components/ScoreRing";

export default function SharedReport() {
  const params = useParams<{ token: string }>();
  const [report, setReport] = useState<{ overall_score: number; summary: string; disclaimer: string } | null>(null);
  const [error, setError] = useState("");
  useEffect(() => {
    api<{ overall_score: number; summary: string; disclaimer: string }>(`/api/reports/shared/${params.token}`)
      .then(setReport)
      .catch(() => setError("This share link is unavailable."));
  }, [params.token]);
  if (error) return <p className="p-8">{error}</p>;
  if (!report) return <p className="p-8">Loading shared report…</p>;
  return (
    <main className="mx-auto max-w-2xl px-4 py-12">
      <h1 className="font-serif text-3xl">Shared analysis</h1>
      <div className="mt-6"><ScoreRing score={report.overall_score} /></div>
      <p className="mt-4 leading-7">{report.summary}</p>
      <p className="mt-4 text-sm text-[var(--ink)]/60">{report.disclaimer}</p>
    </main>
  );
}
