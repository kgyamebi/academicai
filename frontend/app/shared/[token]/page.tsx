"use client";

import { FormEvent, useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { api } from "@/lib/api";
import { ScoreRing } from "@/components/ScoreRing";

type Shared = { overall_score: number; summary: string; disclaimer: string };

export default function SharedReport() {
  const params = useParams<{ token: string }>();
  const [report, setReport] = useState<Shared | null>(null);
  const [error, setError] = useState("");
  const [needsPassword, setNeedsPassword] = useState(false);

  useEffect(() => {
    api<Shared>(`/api/reports/shared/${params.token}`)
      .then(setReport)
      .catch((err: Error) => {
        if (/password/i.test(err.message)) setNeedsPassword(true);
        else setError("This share link is unavailable.");
      });
  }, [params.token]);

  async function unlock(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = new FormData(e.currentTarget);
    try {
      const data = await api<Shared>(`/api/reports/shared/${params.token}`, {
        method: "POST",
        body: JSON.stringify({ password: form.get("password") }),
      });
      setReport(data);
      setNeedsPassword(false);
      setError("");
    } catch {
      setError("Incorrect share password.");
    }
  }

  if (needsPassword && !report) {
    return (
      <main className="mx-auto max-w-md px-4 py-16">
        <h1 className="font-serif text-3xl">Protected report</h1>
        <form onSubmit={unlock} className="mt-6 space-y-4">
          <label className="block text-sm">Password
            <input name="password" type="password" required className="mt-1 w-full rounded-md border border-[var(--rule)] bg-white p-3" />
          </label>
          {error && <p className="text-sm text-[var(--crimson)]" role="alert">{error}</p>}
          <button type="submit" className="w-full rounded-md bg-[var(--teal)] py-3 text-white">Open report</button>
        </form>
      </main>
    );
  }
  if (error) return <p className="p-8">{error}</p>;
  if (!report) return <p className="p-8">Loading shared report…</p>;
  return (
    <main className="mx-auto max-w-2xl px-4 py-12">
      <h1 className="font-serif text-3xl">Shared analysis</h1>
      <div className="mt-6"><ScoreRing score={report.overall_score} /></div>
      <p className="mt-4 leading-7">{report.summary}</p>
      <p className="mt-4 text-sm text-[var(--ink-muted)]">{report.disclaimer}</p>
    </main>
  );
}
