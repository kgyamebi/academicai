"use client";

import { FormEvent, useState } from "react";
import { SiteHeader } from "@/components/SiteHeader";
import { api } from "@/lib/api";

export default function ForgotPage() {
  const [done, setDone] = useState(false);
  async function onSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = new FormData(e.currentTarget);
    await api("/api/auth/password/forgot", { method: "POST", body: JSON.stringify({ email: form.get("email") }) });
    setDone(true);
  }
  return (
    <>
      <SiteHeader compact />
      <main className="mx-auto max-w-md px-4 py-16">
        <h1 className="font-serif text-3xl">Reset password</h1>
        {done ? (
          <p className="mt-6 text-sm">If an account exists, a reset link has been sent.</p>
        ) : (
          <form onSubmit={onSubmit} className="mt-8 space-y-4">
            <label className="block text-sm">Email
              <input name="email" type="email" required className="mt-1 w-full rounded-md border border-[var(--rule)] bg-white p-3" />
            </label>
            <button className="w-full rounded-md bg-[var(--teal)] py-3 text-white">Send reset link</button>
          </form>
        )}
      </main>
    </>
  );
}
