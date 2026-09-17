"use client";

import { FormEvent, useEffect, useState } from "react";
import Link from "next/link";
import { useAuth } from "@/components/AuthProvider";
import { PasswordField } from "@/components/PasswordField";
import { SiteHeader } from "@/components/SiteHeader";
import { SocialAuthButtons } from "@/components/SocialAuthButtons";
import { api, track } from "@/lib/api";
import { trackAdsSignup } from "@/lib/ads";

export default function RegisterPage() {
  const { signedIn, status } = useAuth();
  const [error, setError] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");

  useEffect(() => {
    if (status === "ready" && signedIn) {
      window.location.replace("/app/dashboard");
    }
  }, [status, signedIn]);

  async function onSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setError("");
    if (password !== confirm) {
      setError("Passwords do not match. Re-type them carefully.");
      return;
    }
    if (password.length < 8) {
      setError("Use at least 8 characters for your password.");
      return;
    }
    const form = new FormData(e.currentTarget);
    const email = String(form.get("email") || "");
    try {
      await api("/api/auth/register", {
        method: "POST",
        body: JSON.stringify({
          email,
          password,
          full_name: form.get("full_name"),
          country: form.get("country"),
        }),
      });
      track("signup", "/register");
      // Land on onboarding with ?signup=1 so the beacon can fire on a stable page
      // (immediate redirect used to cancel the Ads conversion ping).
      await trackAdsSignup({ email, method: "email" });
      window.location.href = "/onboarding?signup=1";
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
          <PasswordField
            id="password"
            name="password"
            label="Password"
            autoComplete="new-password"
            minLength={8}
            required
            invalid={Boolean(error)}
            describedBy={error ? "password-hint register-error" : "password-hint"}
            value={password}
            onChange={setPassword}
          />
          <p id="password-hint" className="text-sm text-[var(--ink-muted)]">
            Use at least 8 characters. Tap the eye to show what you typed.
          </p>
          <PasswordField
            id="password_confirm"
            name="password_confirm"
            label="Confirm password"
            autoComplete="new-password"
            minLength={8}
            required
            invalid={Boolean(error)}
            describedBy={error ? "register-error" : undefined}
            value={confirm}
            onChange={setConfirm}
          />
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
