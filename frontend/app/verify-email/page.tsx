"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState } from "react";
import { SiteHeader } from "@/components/SiteHeader";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/Button";

type State = "pending" | "success" | "expired" | "invalid" | "missing";

function VerifyInner() {
  const params = useSearchParams();
  const [state, setState] = useState<State>("pending");
  const [detail, setDetail] = useState("Confirming your email…");

  useEffect(() => {
    const token = params.get("token");
    if (!token) {
      setState("missing");
      setDetail("This verification link is missing a token. Open the link from your email, or request a new one from Settings.");
      return;
    }
    api<{ ok?: boolean }>("/api/auth/verify-email", { method: "POST", body: JSON.stringify({ token }) })
      .then(() => {
        setState("success");
        setDetail("Your email is verified. Full AcademicCheck AI features are unlocked.");
      })
      .catch((e) => {
        const msg = e instanceof Error ? e.message.toLowerCase() : "";
        if (msg.includes("expired")) {
          setState("expired");
          setDetail("This verification link has expired. Sign in and resend a fresh email.");
        } else {
          setState("invalid");
          setDetail("This verification link is invalid or was already used. Request a new one from Settings.");
        }
      });
  }, [params]);

  const title =
    state === "success"
      ? "Email verified"
      : state === "expired"
        ? "Link expired"
        : state === "invalid"
          ? "Verification failed"
          : state === "missing"
            ? "Verification pending"
            : "Verifying email";

  return (
    <div className="mt-8 space-y-5">
      <p className="text-sm leading-7 text-[var(--ink-muted)]" role="status" aria-live="polite">
        {detail}
      </p>
      {state === "success" ? (
        <div className="flex flex-wrap gap-3">
          <Link href="/app/dashboard">
            <Button type="button">Open dashboard</Button>
          </Link>
          <Link href="/app/settings">
            <Button type="button" variant="secondary">
              Account settings
            </Button>
          </Link>
        </div>
      ) : null}
      {state === "expired" || state === "invalid" || state === "missing" ? (
        <div className="flex flex-wrap gap-3">
          <Link href="/login">
            <Button type="button">Sign in</Button>
          </Link>
          <Link href="/app/settings">
            <Button type="button" variant="secondary">
              Resend from settings
            </Button>
          </Link>
        </div>
      ) : null}
      <p className="sr-only">{title}</p>
    </div>
  );
}

export default function VerifyEmailPage() {
  return (
    <>
      <SiteHeader compact />
      <main id="main-content" tabIndex={-1} className="mx-auto max-w-lg px-4 py-16">
        <p className="text-sm font-medium tracking-wide text-[var(--teal)]">AcademicCheck AI</p>
        <h1 className="mt-2 font-serif text-3xl md:text-4xl">Verify your email</h1>
        <p className="mt-3 text-sm leading-7 text-[var(--ink-muted)]">
          Confirm ownership of your address to unlock PDF exports, sharing, advanced history, and future premium
          plans.
        </p>
        <Suspense fallback={<p className="mt-8 text-sm text-[var(--ink-muted)]">Loading…</p>}>
          <VerifyInner />
        </Suspense>
      </main>
    </>
  );
}
