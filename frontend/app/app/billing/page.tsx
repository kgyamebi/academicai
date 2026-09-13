"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import { ButtonLink } from "@/components/ui/Button";
import { Skeleton } from "@/components/ui/EmptyState";

type Billing = {
  plan: { slug: string; name: string; checks_per_month: number; max_words: number };
  subscription: { status: string; checks_used: number; period_end?: string | null };
  credits: number;
};

/** Public free launch: purchases intentionally unavailable. */
export default function BillingPage() {
  const [data, setData] = useState<Billing | null>(null);
  const [message, setMessage] = useState("");

  useEffect(() => {
    api<Billing>("/api/billing")
      .then(setData)
      .catch(() => setMessage("We couldn’t load plan usage. Refresh and try again."));
  }, []);

  if (!data && message) {
    return (
      <main>
        <h1 className="font-serif text-3xl">Plan usage</h1>
        <p role="alert" className="mt-4 text-[var(--crimson)]">
          {message}
        </p>
      </main>
    );
  }

  if (!data) {
    return (
      <main aria-busy="true">
        <h1 className="font-serif text-3xl">Plan usage</h1>
        <div className="mt-8 space-y-3">
          <Skeleton className="h-32 w-full max-w-2xl" />
        </div>
      </main>
    );
  }

  return (
    <main className="mx-auto max-w-3xl space-y-8">
      <div>
        <p className="text-sm font-medium tracking-wide text-[var(--teal)]">Free public launch</p>
        <h1 className="mt-2 font-serif text-3xl md:text-4xl">Plan usage</h1>
        <p className="mt-3 max-w-2xl text-sm leading-7 text-[var(--ink-muted)]">
          Subscriptions and checkout are disabled for this launch. You can still see your current plan limits and usage.
        </p>
      </div>

      <section className="ac-surface p-6" aria-labelledby="current-plan">
        <h2 id="current-plan" className="font-serif text-2xl">
          Current plan
        </h2>
        <p className="mt-3 text-sm leading-7">
          <span className="font-medium">{data.plan.name}</span>
          {" · "}
          {data.subscription.checks_used}/{data.plan.checks_per_month} checks used
          {" · "}
          {Math.round(data.credits)} credits
        </p>
      </section>

      <section className="rounded-[var(--radius-md)] border border-dashed border-[var(--rule)] bg-[var(--paper-2)] p-6" role="status">
        <h2 className="font-serif text-xl">Purchases unavailable</h2>
        <p className="mt-2 text-sm leading-7 text-[var(--ink-muted)]">
          Paid upgrades are intentionally off. There are no checkout buttons in this release — so you never hit a dead
          payment flow.
        </p>
        <div className="mt-4 flex flex-wrap gap-3">
          <ButtonLink href="/check" variant="primary">
            Continue checking
          </ButtonLink>
          <ButtonLink href="/pricing" variant="secondary">
            Free launch details
          </ButtonLink>
        </div>
      </section>

      <p className="text-sm text-[var(--ink-muted)]">
        Questions?{" "}
        <Link href="/contact" className="text-[var(--teal)] underline-offset-4 hover:underline">
          Contact us
        </Link>
      </p>
    </main>
  );
}
