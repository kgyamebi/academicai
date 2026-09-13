"use client";

import { FormEvent, useState } from "react";
import Link from "next/link";
import { SiteHeader } from "@/components/SiteHeader";
import { api, track } from "@/lib/api";

export default function LoginPage() {
  const [error, setError] = useState("");
  async function onSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = new FormData(e.currentTarget);
    try {
      await api("/api/auth/login", {
        method: "POST",
        body: JSON.stringify({ email: form.get("email"), password: form.get("password") }),
      });
      track("login", "/login");
      window.location.href = "/app/dashboard";
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not sign in.");
    }
  }
  return (
    <>
      <SiteHeader compact />
      <main id="main-content" tabIndex={-1} className="mx-auto max-w-md px-4 py-16">
        <h1 className="font-serif text-3xl">Sign in</h1>
        <form onSubmit={onSubmit} className="mt-8 space-y-4" noValidate>
          <label className="block text-sm" htmlFor="email">Email
            <input id="email" name="email" type="email" autoComplete="email" required aria-invalid={Boolean(error)} aria-describedby={error ? "login-error" : undefined} className="mt-1 w-full rounded-md border border-[var(--rule)] bg-white p-3" />
          </label>
          <label className="block text-sm" htmlFor="password">Password
            <input id="password" name="password" type="password" autoComplete="current-password" required aria-invalid={Boolean(error)} aria-describedby={error ? "login-error" : undefined} className="mt-1 w-full rounded-md border border-[var(--rule)] bg-white p-3" />
          </label>
          {error && <p id="login-error" className="text-sm text-[var(--crimson)]" role="alert">{error}</p>}
          <button type="submit" className="ac-hit w-full rounded-md bg-[var(--teal)] text-white">Continue</button>
        </form>
        <p className="mt-4 text-sm"><Link href="/forgot-password" className="underline">Forgot password</Link></p>
        <p className="mt-2 text-sm">New here? <Link href="/register" className="underline">Create a free account</Link></p>
      </main>
    </>
  );
}
