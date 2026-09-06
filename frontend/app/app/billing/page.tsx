"use client";

import { useEffect, useState } from "react";
import { api, track } from "@/lib/api";

type Billing = {
  plan: { slug: string; name: string; checks_per_month: number; max_words: number };
  subscription: { status: string; checks_used: number };
  credits: number;
};

export default function BillingPage() {
  const [data, setData] = useState<Billing | null>(null);
  const [message, setMessage] = useState("");
  useEffect(() => {
    api<Billing>("/api/billing").then(setData);
  }, []);
  async function subscribe(slug: string) {
    const result = await api<{ checkout_url?: string; message?: string }>("/api/billing/checkout", {
      method: "POST",
      body: JSON.stringify({ plan_slug: slug, provider: "stripe", currency: "USD" }),
    });
    if (result.checkout_url) {
      window.location.href = result.checkout_url;
      return;
    }
    setMessage(result.message || "Checkout could not start. Payment keys may be missing.");
    track("subscription_started", "/app/billing");
  }
  if (!data) return <p>Loading billing…</p>;
  return (
    <main className="max-w-xl">
      <h1 className="font-serif text-3xl">Billing</h1>
      <p className="mt-3 text-sm">Current plan: {data.plan.name} · {data.subscription.checks_used}/{data.plan.checks_per_month} checks used</p>
      <p className="text-sm">Credits: {data.credits}</p>
      <div className="mt-6 flex gap-3">
        <button onClick={() => subscribe("student")} className="rounded-md bg-[var(--teal)] px-4 py-2 text-white">Upgrade to Student ($1.99)</button>
        <button onClick={() => subscribe("pro")} className="rounded-md border border-[var(--rule)] px-4 py-2">Pro Student ($3.99)</button>
      </div>
      {message && <p className="mt-4 text-sm">{message}</p>}
    </main>
  );
}
