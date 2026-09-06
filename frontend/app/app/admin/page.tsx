"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";

export default function AdminPage() {
  const [data, setData] = useState<Record<string, number> | null>(null);
  const [error, setError] = useState("");
  useEffect(() => {
    api<Record<string, number>>("/api/admin/overview")
      .then(setData)
      .catch((e) => setError(e.message));
  }, []);
  if (error) return <p>Admin access is restricted. {error}</p>;
  if (!data) return <p>Loading admin…</p>;
  return (
    <main>
      <h1 className="font-serif text-3xl">Admin</h1>
      <ul className="mt-6 grid gap-3 sm:grid-cols-2">
        {Object.entries(data).map(([k, v]) => (
          <li key={k} className="rounded-lg border border-[var(--rule)] p-4">
            <p className="text-xs uppercase">{k.replaceAll("_", " ")}</p>
            <p className="font-serif text-2xl">{v}</p>
          </li>
        ))}
      </ul>
    </main>
  );
}
