"use client";

import { FormEvent, useState } from "react";
import { useSearchParams } from "next/navigation";
import { Suspense } from "react";
import { SiteHeader } from "@/components/SiteHeader";
import { api } from "@/lib/api";

function ResetInner() {
  const params = useSearchParams();
  const [done, setDone] = useState(false);
  async function onSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = new FormData(e.currentTarget);
    await api("/api/auth/password/reset", {
      method: "POST",
      body: JSON.stringify({ token: params.get("token"), password: form.get("password") }),
    });
    setDone(true);
  }
  return done ? (
    <p className="mt-6" role="status" aria-live="polite">Password updated. You can sign in.</p>
  ) : (
    <form onSubmit={onSubmit} className="mt-8 space-y-4">
      <label className="block text-sm" htmlFor="password">New password
        <input id="password" name="password" type="password" autoComplete="new-password" minLength={8} required className="mt-1 w-full rounded-md border border-[var(--rule)] bg-white p-3" />
      </label>
      <button type="submit" className="ac-hit w-full rounded-md bg-[var(--teal)] text-white">Update password</button>
    </form>
  );
}

export default function ResetPage() {
  return (
    <>
      <SiteHeader compact />
      <main id="main-content" tabIndex={-1} className="mx-auto max-w-md px-4 py-16">
        <h1 className="font-serif text-3xl">Choose a new password</h1>
        <Suspense><ResetInner /></Suspense>
      </main>
    </>
  );
}
