"use client";

import { useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState } from "react";
import { SiteHeader } from "@/components/SiteHeader";
import { api } from "@/lib/api";

function VerifyInner() {
  const params = useSearchParams();
  const [state, setState] = useState("Verifying…");
  useEffect(() => {
    const token = params.get("token");
    if (!token) {
      setState("This verification link is missing.");
      return;
    }
    api("/api/auth/verify", { method: "POST", body: JSON.stringify({ token }) })
      .then(() => setState("Email verified. You can sign in."))
      .catch(() => setState("This verification link is invalid or expired."));
  }, [params]);
  return <p className="mt-6">{state}</p>;
}

export default function VerifyPage() {
  return (
    <>
      <SiteHeader compact />
      <main className="mx-auto max-w-md px-4 py-16">
        <h1 className="font-serif text-3xl">Verify email</h1>
        <Suspense>
          <VerifyInner />
        </Suspense>
      </main>
    </>
  );
}
