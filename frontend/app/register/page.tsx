"use client";

import { FormEvent, useEffect, useState } from "react";
import Link from "next/link";
import { AuthShell } from "@/components/AmbientStage";
import { useAuth } from "@/components/AuthProvider";
import { BrandMark } from "@/components/BrandMark";
import { PasswordField } from "@/components/PasswordField";
import { SiteHeader } from "@/components/SiteHeader";
import { SocialAuthButtons } from "@/components/SocialAuthButtons";
import { api, track } from "@/lib/api";

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
      window.location.href = "/onboarding?signup=1";
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not create the account.");
    }
  }

  return (
    <>
      <SiteHeader compact />
      <main id="main-content" tabIndex={-1}>
        <AuthShell
          eyebrow="Start free"
          title="Create your account"
          subtitle="Save assignments, reports and draft history. We do not use your work for model training unless you opt in."
        >
          <div className="mb-6 flex justify-center">
            <BrandMark className="h-14 w-14" />
          </div>
          <SocialAuthButtons next="/onboarding" />
          <form onSubmit={onSubmit} className="mt-2 space-y-4">
            <label className="block text-sm" htmlFor="full_name">
              Full name
              <input id="full_name" name="full_name" autoComplete="name" required className="ac-field mt-1" />
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
                className="ac-field mt-1"
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
                className="ac-field mt-1"
              />
            </label>
            {error && (
              <p id="register-error" className="text-sm text-[var(--crimson)]" role="alert">
                {error}
              </p>
            )}
            <button type="submit" className="ac-hit ac-btn-micro w-full rounded-md bg-[var(--teal)] text-white">
              Continue with Email
            </button>
          </form>
          <p className="mt-4 text-sm text-[var(--ink-muted)]">
            Already registered?{" "}
            <Link href="/login" className="text-[var(--teal)] underline-offset-4 hover:underline">
              Sign in
            </Link>
          </p>
        </AuthShell>
      </main>
    </>
  );
}
