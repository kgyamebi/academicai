"use client";

import { FormEvent, useState } from "react";
import Link from "next/link";
import { SiteHeader } from "@/components/SiteHeader";
import { api, setTokens, track } from "@/lib/api";

export default function RegisterPage() {
  const [error, setError] = useState("");
  async function onSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = new FormData(e.currentTarget);
    try {
      const data = await api<{ access_token: string; refresh_token: string }>("/api/auth/register", {
        method: "POST",
        body: JSON.stringify({
          email: form.get("email"),
          password: form.get("password"),
          full_name: form.get("full_name"),
          country: form.get("country"),
        }),
      });
      setTokens(data.access_token, data.refresh_token);
      track("signup", "/register");
      window.location.href = "/app/dashboard";
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not create the account.");
    }
  }
  return (
    <>
      <SiteHeader compact />
      <main className="mx-auto max-w-md px-4 py-16">
        <h1 className="font-serif text-3xl">Create a free account</h1>
        <p className="mt-2 text-sm text-[var(--ink)]/70">Save assignments, reports and draft history. We do not use your work for model training unless you opt in.</p>
        <form onSubmit={onSubmit} className="mt-8 space-y-4">
          <label className="block text-sm">Full name
            <input name="full_name" required className="mt-1 w-full rounded-md border border-[var(--rule)] bg-white p-3" />
          </label>
          <label className="block text-sm">Email
            <input name="email" type="email" required className="mt-1 w-full rounded-md border border-[var(--rule)] bg-white p-3" />
          </label>
          <label className="block text-sm">Password
            <input name="password" type="password" minLength={8} required className="mt-1 w-full rounded-md border border-[var(--rule)] bg-white p-3" />
          </label>
          <label className="block text-sm">Country (optional)
            <input name="country" maxLength={8} placeholder="GH, NG, US, GB…" className="mt-1 w-full rounded-md border border-[var(--rule)] bg-white p-3" />
          </label>
          {error && <p className="text-sm text-[var(--crimson)]" role="alert">{error}</p>}
          <button className="w-full rounded-md bg-[var(--teal)] py-3 text-white">Create account</button>
        </form>
        <p className="mt-4 text-sm">Already registered? <Link href="/login" className="underline">Sign in</Link></p>
      </main>
    </>
  );
}
