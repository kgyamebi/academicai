"use client";

import { FormEvent, useState } from "react";
import { AuthShell } from "@/components/AmbientStage";
import { BrandMark } from "@/components/BrandMark";
import { SiteHeader } from "@/components/SiteHeader";
import { api } from "@/lib/api";

export default function ForgotPage() {
  const [done, setDone] = useState(false);
  async function onSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = new FormData(e.currentTarget);
    await api("/api/auth/password/forgot", {
      method: "POST",
      body: JSON.stringify({ email: form.get("email") }),
    });
    setDone(true);
  }
  return (
    <>
      <SiteHeader compact />
      <main id="main-content" tabIndex={-1}>
        <AuthShell
          eyebrow="Account recovery"
          title="Reset password"
          subtitle="We’ll email a secure link if an account exists for that address."
        >
          <div className="mb-6 flex justify-center">
            <BrandMark className="h-12 w-12" />
          </div>
          {done ? (
            <p className="text-sm leading-7 text-[var(--ink)]" role="status" aria-live="polite">
              If an account exists, a reset link has been sent. Check your inbox and spam folder.
            </p>
          ) : (
            <form onSubmit={onSubmit} className="space-y-4">
              <label className="block text-sm" htmlFor="email">
                Email
                <input
                  id="email"
                  name="email"
                  type="email"
                  autoComplete="email"
                  required
                  className="ac-field mt-1"
                />
              </label>
              <button type="submit" className="ac-hit ac-btn-micro w-full rounded-md bg-[var(--teal)] text-white">
                Send reset link
              </button>
            </form>
          )}
        </AuthShell>
      </main>
    </>
  );
}
