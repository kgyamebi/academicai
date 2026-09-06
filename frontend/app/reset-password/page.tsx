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
    <p className="mt-6">Password updated. You can sign in.</p>
  ) : (
    <form onSubmit={onSubmit} className="mt-8 space-y-4">
      <label className="block text-sm">New password
        <input name="password" type="password" minLength={8} required className="mt-1 w-full rounded-md border border-[var(--rule)] bg-white p-3" />
      </label>
      <button type="submit" className="w-full rounded-md bg-[var(--teal)] py-3 text-white">Update password</button>
    </form>
  );
}

export default function ResetPage() {
  return (
    <>
      <SiteHeader compact />
      <main className="mx-auto max-w-md px-4 py-16">
        <h1 className="font-serif text-3xl">Choose a new password</h1>
        <Suspense><ResetInner /></Suspense>
      </main>
    </>
  );
}
