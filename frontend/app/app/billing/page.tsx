"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import { ButtonLink } from "@/components/ui/Button";
import { Skeleton } from "@/components/ui/EmptyState";

type Billing = {
  plan: { slug: string; name: string; checks_per_month: number | null; max_words: number; unlimited?: boolean };
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
        <p className="text-sm font-medium tracking-wide text-[var(--teal)]">Fully free</p>
        <h1 className="mt-2 font-serif text-3xl md:text-4xl">Plan usage</h1>
        <p className="mt-3 max-w-2xl text-sm leading-7 text-[var(--ink-muted)]">
          Every feature is free. There is no monthly check cap and no checkout.
        </p>
      </div>

      <section className="ac-surface p-6" aria-labelledby="current-plan">
        <h2 id="current-plan" className="font-serif text-2xl">
          Current plan
        </h2>
        <p className="mt-3 text-sm leading-7">
          <span className="font-medium">{data.plan.name}</span>
          {" · "}
          {data.plan.unlimited || data.plan.checks_per_month == null
            ? "Unlimited checks"
            : `${data.subscription.checks_used}/${data.plan.checks_per_month} checks used`}
        </p>
      </section>

      <section className="rounded-[var(--radius-md)] border border-dashed border-[var(--rule)] bg-[var(--paper-2)] p-6" role="status">
        <h2 className="font-serif text-xl">Purchases unavailable</h2>
        <p className="mt-2 text-sm leading-7 text-[var(--ink-muted)]">
          Paid upgrades are off. Full analysis, coach, PDF export, sharing, and draft comparison are included.
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
