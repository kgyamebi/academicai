"use client";

import { FormEvent, Suspense, useEffect, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { AuthShell } from "@/components/AmbientStage";
import { useAuth } from "@/components/AuthProvider";
import { BrandMark } from "@/components/BrandMark";
import { PasswordField } from "@/components/PasswordField";
import { SiteHeader } from "@/components/SiteHeader";
import { SocialAuthButtons } from "@/components/SocialAuthButtons";
import { api, track } from "@/lib/api";

function LoginForm() {
  const params = useSearchParams();
  const oauthError = params.get("error") || "";
  const { signedIn, status } = useAuth();
  const [error, setError] = useState(oauthError);

  useEffect(() => {
    if (status === "ready" && signedIn) {
      window.location.replace("/app/dashboard");
    }
  }, [status, signedIn]);

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
    <AuthShell
      eyebrow="Welcome back"
      title="Sign in"
      subtitle="Pick up your workspace — reports, drafts, and Fix-First actions waiting."
    >
      <div className="mb-6 flex justify-center">
        <BrandMark className="h-14 w-14" animated />
      </div>
      <SocialAuthButtons next="/app/dashboard" />
      <form onSubmit={onSubmit} className="mt-2 space-y-4" noValidate>
        <label className="block text-sm" htmlFor="email">
          Email
          <input
            id="email"
            name="email"
            type="email"
            autoComplete="email"
            required
            aria-invalid={Boolean(error)}
            aria-describedby={error ? "login-error" : undefined}
            className="ac-field mt-1"
          />
        </label>
        <PasswordField
          id="password"
          name="password"
          label="Password"
          autoComplete="current-password"
          required
          invalid={Boolean(error)}
          describedBy={error ? "login-error" : undefined}
        />
        {error && (
          <p id="login-error" className="text-sm text-[var(--crimson)]" role="alert">
            {error}
          </p>
        )}
        <button type="submit" className="ac-hit ac-btn-micro w-full rounded-md bg-[var(--teal)] text-white">
          Continue with Email
        </button>
      </form>
      <p className="mt-4 text-sm">
        <Link href="/forgot-password" className="text-[var(--teal)] underline-offset-4 hover:underline">
          Forgot password
        </Link>
      </p>
      <p className="mt-2 text-sm text-[var(--ink-muted)]">
        New here?{" "}
        <Link href="/register" className="text-[var(--teal)] underline-offset-4 hover:underline">
          Create a free account
        </Link>
      </p>
    </AuthShell>
  );
}

export default function LoginPage() {
  return (
    <>
      <SiteHeader compact />
      <main id="main-content" tabIndex={-1}>
        <Suspense
          fallback={
            <div className="mx-auto max-w-md px-4 py-16">
              <h1 className="font-serif text-3xl">Sign in</h1>
            </div>
          }
        >
          <LoginForm />
        </Suspense>
      </main>
    </>
  );
}
