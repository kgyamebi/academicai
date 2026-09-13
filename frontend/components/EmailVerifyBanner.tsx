"use client";

import Link from "next/link";
import { useState } from "react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/Button";

export function EmailVerifyBanner({ email }: { email: string }) {
  const [status, setStatus] = useState<"idle" | "sending" | "sent" | "error">("idle");
  const [error, setError] = useState("");

  async function resend() {
    setStatus("sending");
    setError("");
    try {
      await api("/api/auth/resend-verification", { method: "POST", body: JSON.stringify({}) });
      setStatus("sent");
    } catch (e) {
      setStatus("error");
      setError(e instanceof Error ? e.message : "Could not resend verification email.");
    }
  }

  return (
    <div
      className="mb-6 rounded-[var(--radius-sm)] border border-[var(--amber)]/30 bg-amber-50 px-3 py-3 text-sm text-[var(--amber)]"
      role="status"
      aria-live="polite"
    >
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <p className="font-medium text-[var(--ink)]">Verify your email to unlock all AcademicCheck AI features</p>
          <p className="mt-1 text-[var(--ink-muted)]">
            PDF exports, sharing, version history, and future billing stay locked until{" "}
            <span className="text-[var(--ink)]">{email}</span> is confirmed.{" "}
            <Link href="/verify-email" className="text-[var(--teal)] underline-offset-2 hover:underline">
              Verification help
            </Link>
          </p>
          {status === "sent" ? (
            <p className="mt-1 text-[var(--forest)]">Verification email sent — check your inbox.</p>
          ) : null}
          {status === "error" ? <p className="mt-1 text-[var(--crimson)]">{error}</p> : null}
        </div>
        <Button type="button" variant="secondary" className="shrink-0" busy={status === "sending"} onClick={resend}>
          Resend email
        </Button>
      </div>
    </div>
  );
}
