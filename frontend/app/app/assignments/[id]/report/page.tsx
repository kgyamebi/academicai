"use client";

import { useEffect, useMemo, useState } from "react";
import { useParams, useSearchParams } from "next/navigation";
import { FindingCard } from "@/components/FindingCard";
import { ScoreRing } from "@/components/ScoreRing";
import { api, getToken, track } from "@/lib/api";
import { apiUrl } from "@/lib/utils";

type Report = {
  id: string;
  overall_score: number;
  summary: string;
  disclaimer: string;
  strengths: string[];
  weaknesses: string[];
  priority_actions: string[];
  structure_map: { key: string; label: string; status: string }[];
  question: { interpretation?: string; command_words?: string[]; required?: string[] };
  scores: { category: string; score: number; weight: number; rationale: string }[];
  findings: {
    id: string;
    category: string;
    severity: string;
    location: string;
    explanation: string;
    suggestion: string;
    teaching_note?: string;
    example?: string;
    original_text?: string;
  }[];
  word_count: Record<string, number>;
  readability: { score?: number; explanation?: string };
  weakest_area: { category?: string; explanation?: string; how_to_improve?: string; example?: string; teaching_note?: string };
  rubric?: { estimated_total?: number; label?: string; criteria?: { name: string; awarded: number; max_points: number }[] };
};

export default function ReportPage() {
  const params = useParams<{ id: string }>();
  const search = useSearchParams();
  const [report, setReport] = useState<Report | null>(null);
  const [tab, setTab] = useState<"document" | "findings" | "score" | "coach">("score");
  const [selected, setSelected] = useState<Report["findings"][number] | null>(null);
  const [mode, setMode] = useState<"explain" | "suggest" | "teach" | "example">("explain");
  const reportId = search.get("report");

  useEffect(() => {
    if (!reportId) return;
    api<Report>(`/api/reports/${reportId}`).then((r) => {
      setReport(r);
      track("report_viewed", "/app/report");
    });
  }, [reportId]);

  const selectedText = useMemo(() => {
    if (!selected) return "";
    if (mode === "suggest") return selected.suggestion;
    if (mode === "teach") return selected.teaching_note || "This finding is about academic writing quality, not a hidden lecturer rule.";
    if (mode === "example") return selected.example || "Example: turn 'This essay is about X' into a contestable claim that answers the question.";
    return selected.explanation;
  }, [selected, mode]);

  if (!report) return <p>Loading report…</p>;

  async function downloadPdf() {
    const token = getToken();
    const res = await fetch(`${apiUrl()}/api/reports/${report!.id}/pdf`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "academiccheck-report.pdf";
    a.click();
  }

  return (
    <main className="lg:grid lg:grid-cols-[1.1fr_0.9fr] lg:gap-8">
      <section>
        <div className="mb-4 flex gap-2 lg:hidden">
          {(["score", "findings", "document", "coach"] as const).map((t) => (
            <button key={t} onClick={() => setTab(t)} className={`rounded-md px-3 py-1 text-sm ${tab === t ? "bg-[var(--teal)] text-white" : "border border-[var(--rule)]"}`}>
              {t}
            </button>
          ))}
        </div>
        <div className={tab === "score" || tab === "document" ? "" : "hidden lg:block"}>
          <ScoreRing score={report.overall_score} />
          <p className="mt-4 max-w-xl text-sm leading-6">{report.summary}</p>
          <p className="mt-2 text-xs text-[var(--ink)]/60">{report.disclaimer}</p>
          <div className="mt-6 grid grid-cols-2 gap-2">
            {report.scores.map((s) => (
              <div key={s.category} className="rounded-md border border-[var(--rule)] bg-[var(--paper-2)] p-3">
                <p className="text-xs uppercase tracking-wide">{s.category.replaceAll("_", " ")}</p>
                <p className="font-serif text-2xl">{s.score}</p>
              </div>
            ))}
          </div>
          <h2 className="mt-8 font-serif text-xl">Structure map</h2>
          <ul className="mt-3 space-y-1 text-sm">
            {report.structure_map.map((s) => (
              <li key={s.key}>
                {s.label} {s.status === "present" ? "✓" : s.status === "warning" ? "⚠" : "✗"}
                <span className="sr-only"> {s.status}</span>
              </li>
            ))}
          </ul>
          <button onClick={downloadPdf} className="mt-6 rounded-md border border-[var(--rule)] px-4 py-2 text-sm">
            Download analysis report
          </button>
        </div>
      </section>
      <section className={tab === "findings" || tab === "score" ? "space-y-4" : "hidden lg:block space-y-4"}>
        <div className="rounded-xl border border-[var(--crimson)]/30 bg-red-50 p-4">
          <p className="text-xs font-semibold uppercase">Fix these first</p>
          <ul className="mt-2 list-disc space-y-1 pl-5 text-sm">
            {report.priority_actions.map((a) => <li key={a}>{a}</li>)}
          </ul>
          <button
            className="mt-4 rounded-md bg-[var(--teal)] px-3 py-2 text-sm text-white"
            onClick={() => {
              const match = report.findings.find((f) => f.category === report.weakest_area.category) || report.findings[0];
              setSelected(match || null);
              setTab("coach");
            }}
          >
            Fix my weakest area
          </button>
        </div>
        <p className="text-sm"><strong>Strong:</strong> {report.strengths.join(", ") || "—"}</p>
        <p className="text-sm"><strong>Needs attention:</strong> {report.weaknesses.join(", ") || "—"}</p>
        {report.findings.map((f) => (
          <FindingCard key={f.id} finding={f} onSelect={() => { setSelected(f); setTab("coach"); }} />
        ))}
      </section>
      {(tab === "coach" || selected) && (
        <aside className="mt-8 rounded-xl border border-[var(--rule)] bg-[var(--paper-2)] p-4 lg:col-span-2">
          <h2 className="font-serif text-xl">{selected ? selected.location : report.weakest_area.category}</h2>
          <div className="mt-3 flex flex-wrap gap-2">
            {(["explain", "suggest", "teach", "example"] as const).map((m) => (
              <button key={m} onClick={() => setMode(m)} className={`rounded-md px-3 py-1 text-sm ${mode === m ? "bg-[var(--teal)] text-white" : "border border-[var(--rule)]"}`}>
                {m === "teach" ? "Teach me" : m[0].toUpperCase() + m.slice(1)}
              </button>
            ))}
          </div>
          <p className="mt-4 text-sm leading-7">{selectedText || report.weakest_area.how_to_improve}</p>
          {selected?.original_text && <blockquote className="mt-4 border-l-2 border-[var(--teal)] pl-3 text-sm italic">{selected.original_text}</blockquote>}
        </aside>
      )}
    </main>
  );
}
