"use client";

import { useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense } from "react";
import { SiteHeader } from "@/components/SiteHeader";

function RedirectInner() {
  const router = useRouter();
  const params = useSearchParams();
  useEffect(() => {
    const token = params.get("token");
    const q = token ? `?token=${encodeURIComponent(token)}` : "";
    router.replace(`/verify-email${q}`);
  }, [params, router]);
  return <p className="mt-6 text-sm text-[var(--ink-muted)]">Redirecting…</p>;
}

/** Legacy `/verify` → canonical `/verify-email` (Invoice App path parity). */
export default function VerifyRedirectPage() {
  return (
    <>
      <SiteHeader compact />
      <main id="main-content" tabIndex={-1} className="mx-auto max-w-md px-4 py-16">
        <h1 className="font-serif text-3xl">Verify email</h1>
        <Suspense>
          <RedirectInner />
        </Suspense>
      </main>
    </>
  );
}
