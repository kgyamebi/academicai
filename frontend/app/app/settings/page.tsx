"use client";

import { api } from "@/lib/api";

export default function SettingsPage() {
  async function deleteAccount() {
    if (!confirm("Delete your account and documents? Financial records required by law may be retained.")) return;
    await api("/api/auth/me", { method: "DELETE" });
    localStorage.clear();
    window.location.href = "/";
  }
  return (
    <main className="max-w-xl">
      <h1 className="font-serif text-3xl">Settings</h1>
      <p className="mt-3 text-sm leading-6">
        Assignments are private to your account. We do not sell documents and we do not use them for model training unless you opt in.
        Guest uploads are deleted automatically after a short retention period.
      </p>
      <button onClick={deleteAccount} className="mt-8 rounded-md border border-[var(--crimson)] px-4 py-2 text-[var(--crimson)]">
        Delete account
      </button>
    </main>
  );
}
