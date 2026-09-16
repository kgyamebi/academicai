"use client";

import { FormEvent, useState } from "react";
import Link from "next/link";
import { SiteHeader } from "@/components/SiteHeader";
import { SocialAuthButtons } from "@/components/SocialAuthButtons";
import { api, track } from "@/lib/api";

export default function RegisterPage() {
  const [error, setError] = useState("");
  async function onSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = new FormData(e.currentTarget);
    try {
      await api("/api/auth/register", {
        method: "POST",
        body: JSON.stringify({
          email: form.get("email"),
          password: form.get("password"),
          full_name: form.get("full_name"),
          country: form.get("country"),
        }),
      });
      track("signup", "/register");
      window.location.href = "/onboarding";
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not create the account.");
    }
  }
  return (
    <>
      <SiteHeader compact />
      <main id="main-content" tabIndex={-1} className="mx-auto max-w-md px-4 py-16">
        <h1 className="font-serif text-3xl">Create a free account</h1>
        <p className="mt-2 text-sm text-[var(--ink-muted)]">
          Save assignments, reports and draft history. We do not use your work for model training unless you opt in.
        </p>
        <div className="mt-8">
          <SocialAuthButtons next="/onboarding" />
        </div>
        <form onSubmit={onSubmit} className="mt-2 space-y-4">
          <label className="block text-sm" htmlFor="full_name">
            Full name
            <input
              id="full_name"
              name="full_name"
              autoComplete="name"
              required
              className="mt-1 w-full rounded-md border border-[var(--rule)] bg-white p-3"
            />
          </label>
          <label className="block text-sm" htmlFor="email">
            Email
            <input
              id="email"
              name="email"
              type="email"
              autoComplete="email"
              required
              aria-invalid={Boolean(error)}
              aria-describedby={error ? "register-error" : undefined}
              className="mt-1 w-full rounded-md border border-[var(--rule)] bg-white p-3"
            />
          </label>
          <label className="block text-sm" htmlFor="password">
            Password
            <input
              id="password"
              name="password"
              type="password"
              autoComplete="new-password"
              minLength={8}
              required
              aria-invalid={Boolean(error)}
              aria-describedby={error ? "password-hint register-error" : "password-hint"}
              className="mt-1 w-full rounded-md border border-[var(--rule)] bg-white p-3"
            />
          </label>
          <p id="password-hint" className="text-sm text-[var(--ink-muted)]">
            Use at least 8 characters. A password manager can fill this field.
          </p>
          <label className="block text-sm" htmlFor="country">
            Country (optional)
            <input
              id="country"
              name="country"
              maxLength={8}
              placeholder="GH, NG, US, GB…"
              className="mt-1 w-full rounded-md border border-[var(--rule)] bg-white p-3"
            />
          </label>
          {error && (
            <p id="register-error" className="text-sm text-[var(--crimson)]" role="alert">
              {error}
            </p>
          )}
          <button type="submit" className="ac-hit w-full rounded-md bg-[var(--teal)] text-white">
            Continue with Email
          </button>
        </form>
        <p className="mt-4 text-sm">
          Already registered?{" "}
          <Link href="/login" className="underline">
            Sign in
          </Link>
        </p>
      </main>
    </>
  );
}
