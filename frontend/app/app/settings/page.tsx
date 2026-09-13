"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/Button";
import { StatusBanner } from "@/components/ui/EmptyState";

type Me = {
  email?: string | null;
  email_verified?: boolean;
  pending_email?: string | null;
  is_guest?: boolean;
};

export default function SettingsPage() {
  const [confirming, setConfirming] = useState(false);
  const [me, setMe] = useState<Me | null>(null);
  const [newEmail, setNewEmail] = useState("");
  const [emailMsg, setEmailMsg] = useState("");
  const [emailBusy, setEmailBusy] = useState(false);
  const [resendBusy, setResendBusy] = useState(false);
  const cancelRef = useRef<HTMLButtonElement>(null);
  const deleteRef = useRef<HTMLButtonElement>(null);
  const confirmDeleteRef = useRef<HTMLButtonElement>(null);
  const dialogRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    api<Me>("/api/auth/me")
      .then(setMe)
      .catch(() => setMe(null));
  }, []);

  useEffect(() => {
    if (!confirming) return;
    cancelRef.current?.focus();
    function onKey(event: KeyboardEvent) {
      if (event.key === "Escape") {
        setConfirming(false);
        deleteRef.current?.focus();
        return;
      }
      if (event.key !== "Tab" || !dialogRef.current) return;
      const focusable = [cancelRef.current, confirmDeleteRef.current].filter(Boolean) as HTMLElement[];
      if (focusable.length < 2) return;
      const first = focusable[0];
      const last = focusable[1];
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [confirming]);

  async function deleteAccount() {
    await api("/api/auth/me", { method: "DELETE" });
    localStorage.clear();
    window.location.href = "/";
  }

  async function resendVerification() {
    setResendBusy(true);
    setEmailMsg("");
    try {
      await api("/api/auth/resend-verification", { method: "POST", body: JSON.stringify({}) });
      setEmailMsg("Verification email sent. Check your inbox.");
    } catch (e) {
      setEmailMsg(e instanceof Error ? e.message : "Could not resend verification.");
    } finally {
      setResendBusy(false);
    }
  }

  async function changeEmail(e: React.FormEvent) {
    e.preventDefault();
    setEmailBusy(true);
    setEmailMsg("");
    try {
      const result = await api<Me & { ok?: boolean }>("/api/auth/email/change", {
        method: "POST",
        body: JSON.stringify({ email: newEmail }),
      });
      setMe((prev) => ({
        ...(prev || {}),
        email: result.email ?? prev?.email,
        pending_email: result.pending_email,
        email_verified: false,
      }));
      setNewEmail("");
      setEmailMsg("We notified your old address and sent a verification link to the new one.");
    } catch (err) {
      setEmailMsg(err instanceof Error ? err.message : "Could not change email.");
    } finally {
      setEmailBusy(false);
    }
  }

  return (
    <main className="mx-auto max-w-xl space-y-8">
      <div>
        <p className="text-sm font-medium tracking-wide text-[var(--teal)]">Account</p>
        <h1 className="mt-2 font-serif text-3xl md:text-4xl">Settings</h1>
        <p id="privacy-note" className="mt-3 text-sm leading-7 text-[var(--ink-muted)]">
          Assignments are private to your account. We do not sell documents and we do not use them for model training
          unless you opt in. Guest uploads are deleted automatically after a short retention period.
        </p>
      </div>

      {me && !me.is_guest ? (
        <section className="ac-surface p-5" aria-labelledby="email-heading">
          <h2 id="email-heading" className="font-serif text-xl">
            Email &amp; verification
          </h2>
          <p className="mt-2 text-sm text-[var(--ink-muted)]">
            Current: <span className="text-[var(--ink)]">{me.email}</span>
            {me.pending_email ? (
              <>
                {" "}
                · Pending: <span className="text-[var(--ink)]">{me.pending_email}</span>
              </>
            ) : null}
          </p>
          {me.email_verified && !me.pending_email ? (
            <StatusBanner tone="success">Email verified</StatusBanner>
          ) : (
            <div className="mt-3 space-y-3">
              <StatusBanner tone="warn">
                Verify your email to unlock PDF exports, sharing, advanced history, and future billing.
              </StatusBanner>
              <Button type="button" variant="secondary" busy={resendBusy} onClick={resendVerification}>
                Resend verification email
              </Button>
            </div>
          )}
          <form className="mt-6 space-y-3" onSubmit={changeEmail}>
            <label className="block text-sm" htmlFor="new-email">
              Change email
              <input
                id="new-email"
                type="email"
                required
                value={newEmail}
                onChange={(ev) => setNewEmail(ev.target.value)}
                className="mt-1 w-full rounded-[var(--radius-sm)] border border-[var(--rule)] bg-[var(--paper)] px-3 py-2"
                placeholder="new@school.edu"
                autoComplete="email"
              />
            </label>
            <p className="text-xs leading-5 text-[var(--ink-muted)]">
              We notify your current address, mark the account unverified, and require confirmation of the new address.
            </p>
            <Button type="submit" busy={emailBusy}>
              Update email
            </Button>
          </form>
          {emailMsg ? (
            <p className="mt-3 text-sm text-[var(--ink-muted)]" role="status">
              {emailMsg}
            </p>
          ) : null}
        </section>
      ) : null}

      <section className="ac-surface p-5" aria-labelledby="privacy-links">
        <h2 id="privacy-links" className="font-serif text-xl">
          Privacy &amp; trust
        </h2>
        <ul className="mt-3 space-y-2 text-sm">
          <li>
            <Link href="/help/privacy" className="text-[var(--teal)] underline-offset-4 hover:underline">
              Privacy and data deletion
            </Link>
          </li>
          <li>
            <Link href="/terms" className="text-[var(--teal)] underline-offset-4 hover:underline">
              Terms of use
            </Link>
          </li>
          <li>
            <Link href="/security" className="text-[var(--teal)] underline-offset-4 hover:underline">
              Security overview
            </Link>
          </li>
        </ul>
      </section>

      <section className="ac-surface p-5" aria-labelledby="danger-heading">
        <h2 id="danger-heading" className="font-serif text-xl">
          Danger zone
        </h2>
        <p className="mt-2 text-sm leading-7 text-[var(--ink-muted)]">
          Deleting your account removes document text from the product. Records required by law may be retained.
        </p>
        <Button
          ref={deleteRef}
          type="button"
          variant="danger"
          className="mt-5"
          aria-describedby="privacy-note"
          aria-expanded={confirming}
          aria-controls="delete-dialog"
          onClick={() => setConfirming(true)}
        >
          Delete account
        </Button>
        {confirming && (
          <div
            ref={dialogRef}
            id="delete-dialog"
            role="alertdialog"
            aria-modal="true"
            aria-labelledby="delete-title"
            aria-describedby="delete-desc"
            className="mt-6 rounded-[var(--radius-md)] border border-[var(--crimson)] bg-[var(--paper-2)] p-4"
          >
            <h3 id="delete-title" className="font-serif text-xl">
              Delete this account?
            </h3>
            <p id="delete-desc" className="mt-2 text-sm leading-6 text-[var(--ink-muted)]">
              This permanently deletes your documents. Press Escape or Cancel to keep the account.
            </p>
            <div className="mt-4 flex flex-wrap gap-3">
              <Button
                ref={cancelRef}
                type="button"
                variant="secondary"
                onClick={() => {
                  setConfirming(false);
                  deleteRef.current?.focus();
                }}
              >
                Cancel
              </Button>
              <Button ref={confirmDeleteRef} type="button" variant="danger" onClick={deleteAccount}>
                Delete account
              </Button>
            </div>
          </div>
        )}
      </section>
    </main>
  );
}
