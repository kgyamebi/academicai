"use client";

import { FormEvent, useState } from "react";
import Link from "next/link";
import { SiteHeader } from "@/components/SiteHeader";
import { api, setTokens, track } from "@/lib/api";

export default function LoginPage() {
  const [error, setError] = useState("");
  async function onSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = new FormData(e.currentTarget);
    try {
      const data = await api<{ access_token: string; refresh_token: string }>("/api/auth/login", {
        method: "POST",
        body: JSON.stringify({ email: form.get("email"), password: form.get("password") }),
      });
      setTokens(data.access_token, data.refresh_token);
      window.location.href = "/app/dashboard";
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not sign in.");
    }
  }
  return (
    <>
      <SiteHeader compact />
      <main className="mx-auto max-w-md px-4 py-16">
        <h1 className="font-serif text-3xl">Sign in</h1>
        <form onSubmit={onSubmit} className="mt-8 space-y-4">
          <label className="block text-sm">Email
            <input name="email" type="email" required className="mt-1 w-full rounded-md border border-[var(--rule)] bg-white p-3" />
          </label>
          <label className="block text-sm">Password
            <input name="password" type="password" required className="mt-1 w-full rounded-md border border-[var(--rule)] bg-white p-3" />
          </label>
          {error && <p className="text-sm text-[var(--crimson)]" role="alert">{error}</p>}
          <button className="w-full rounded-md bg-[var(--teal)] py-3 text-white">Continue</button>
        </form>
        <p className="mt-4 text-sm"><Link href="/forgot-password" className="underline">Forgot password</Link></p>
        <p className="mt-2 text-sm">New here? <Link href="/register" className="underline">Create a free account</Link></p>
      </main>
    </>
  );
}
