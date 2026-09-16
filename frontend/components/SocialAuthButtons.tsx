"use client";

import { useEffect, useState } from "react";

type Provider = "google" | "microsoft";

const LABELS: Record<Provider, string> = {
  google: "Continue with Google",
  microsoft: "Continue with Microsoft",
};

function ProviderIcon({ provider }: { provider: Provider }) {
  if (provider === "google") {
    return (
      <svg className="h-5 w-5" viewBox="0 0 24 24" aria-hidden="true">
        <path
          fill="#EA4335"
          d="M12 10.2v3.6h5.1c-.2 1.2-.9 2.3-1.9 3l3.1 2.4c1.8-1.7 2.9-4.1 2.9-7 0-.7-.1-1.3-.2-1.9H12z"
        />
        <path
          fill="#34A853"
          d="M6.6 14.3l-.7.5-2.4 1.9C5.1 19.3 8.3 21 12 21c2.4 0 4.4-.8 5.9-2.1l-3.1-2.4c-.8.6-1.9.9-2.8.9-2.2 0-4-1.5-4.7-3.5z"
        />
        <path
          fill="#4A90E2"
          d="M3.5 7.3C2.8 8.7 2.4 10.3 2.4 12s.4 3.3 1.1 4.7c0 .1 3.1-2.4 3.1-2.4-.2-.6-.3-1.2-.3-1.9s.1-1.3.3-1.9L3.5 7.3z"
        />
        <path
          fill="#FBBC05"
          d="M12 4.8c1.3 0 2.5.5 3.4 1.3l2.6-2.6C16.4 1.9 14.4 1 12 1 8.3 1 5.1 2.7 3.5 5.3l3.1 2.4C7.9 6.3 9.8 4.8 12 4.8z"
        />
      </svg>
    );
  }
  return (
    <svg className="h-5 w-5" viewBox="0 0 23 23" aria-hidden="true">
      <path fill="#f25022" d="M1 1h10v10H1z" />
      <path fill="#00a4ef" d="M12 1h10v10H12z" />
      <path fill="#7fba00" d="M1 12h10v10H1z" />
      <path fill="#ffb900" d="M12 12h10v10H12z" />
    </svg>
  );
}

export function SocialAuthButtons({ next = "/app/dashboard" }: { next?: string }) {
  // Show both immediately so SSR/curl/first paint include the buttons; prune after providers API responds.
  const [providers, setProviders] = useState<Provider[]>(["google", "microsoft"]);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const res = await fetch("/api/auth/oauth/providers", { credentials: "include" });
        if (!res.ok) return;
        const data = (await res.json()) as { providers?: string[] };
        const list = (data.providers || []).filter((p): p is Provider => p === "google" || p === "microsoft");
        if (!cancelled && list.length > 0) setProviders(list);
        if (!cancelled && list.length === 0) setProviders([]);
      } catch {
        /* keep optimistic buttons if API briefly unreachable */
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  if (providers.length === 0) return null;

  const q = encodeURIComponent(next);

  return (
    <div className="space-y-3">
      {providers.map((provider) => (
        <a
          key={provider}
          href={`/api/auth/oauth/${provider}/start?next=${q}`}
          className="ac-hit flex w-full items-center justify-center gap-3 rounded-md border border-[var(--rule)] bg-[var(--paper-2)] px-4 text-sm font-medium text-[var(--ink)] transition-colors hover:bg-black/[0.03]"
        >
          <ProviderIcon provider={provider} />
          {LABELS[provider]}
        </a>
      ))}
      <div className="relative py-2">
        <div className="absolute inset-0 flex items-center" aria-hidden="true">
          <div className="w-full border-t border-[var(--rule)]" />
        </div>
        <div className="relative flex justify-center text-xs uppercase tracking-[0.14em]">
          <span className="bg-[var(--paper)] px-3 text-[var(--ink-muted)]">or</span>
        </div>
      </div>
    </div>
  );
}
