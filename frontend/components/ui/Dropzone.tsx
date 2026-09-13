"use client";

import { useCallback, useId, useState } from "react";
import { cn } from "@/lib/utils";

const ACCEPT = ".docx,.pdf,.txt,.md";

export function Dropzone({
  file,
  onFile,
  disabled,
}: {
  file: File | null;
  onFile: (file: File | null) => void;
  disabled?: boolean;
}) {
  const id = useId();
  const [over, setOver] = useState(false);
  const [rejectMsg, setRejectMsg] = useState("");

  const take = useCallback(
    (list: FileList | null) => {
      const next = list?.[0] || null;
      setRejectMsg("");
      if (!next) {
        onFile(null);
        return;
      }
      const ok = /\.(docx|pdf|txt|md)$/i.test(next.name);
      if (!ok) {
        setRejectMsg("Please upload a PDF, DOCX, TXT, or MD file.");
        return;
      }
      if (next.size > 15 * 1024 * 1024) {
        setRejectMsg("File is too large. Maximum upload size is 15 MB.");
        return;
      }
      onFile(next);
    },
    [onFile],
  );

  return (
    <div>
      <div
        role="button"
        tabIndex={disabled ? -1 : 0}
        aria-disabled={disabled || undefined}
        aria-describedby={`${id}-hint${rejectMsg ? ` ${id}-reject` : ""}`}
        onKeyDown={(e) => {
          if (disabled) return;
          if (e.key === "Enter" || e.key === " ") {
            e.preventDefault();
            document.getElementById(id)?.click();
          }
        }}
        onDragEnter={(e) => {
          e.preventDefault();
          if (!disabled) setOver(true);
        }}
        onDragOver={(e) => {
          e.preventDefault();
          if (!disabled) setOver(true);
        }}
        onDragLeave={(e) => {
          e.preventDefault();
          setOver(false);
        }}
        onDrop={(e) => {
          e.preventDefault();
          setOver(false);
          if (!disabled) take(e.dataTransfer.files);
        }}
        onClick={() => {
          if (!disabled) document.getElementById(id)?.click();
        }}
        className={cn(
          "ac-hit flex min-h-[160px] cursor-pointer flex-col items-center justify-center gap-2 rounded-[var(--radius-md)] border border-dashed px-6 py-8 text-center transition-colors duration-150",
          over
            ? "border-[var(--teal)] bg-[var(--teal-soft)]"
            : "border-[var(--rule)] bg-[var(--paper-2)] hover:border-[var(--teal)]/50",
          disabled && "pointer-events-none opacity-60",
        )}
      >
        <p className="font-serif text-lg text-[var(--ink)]">
          {over ? "Drop to upload" : file ? file.name : "Drop your draft here"}
        </p>
        <p className="text-sm text-[var(--ink-muted)]">
          {file
            ? `${Math.max(1, Math.round(file.size / 1024))} KB · click to replace`
            : "PDF, DOCX, TXT, or MD · validated by file signature"}
        </p>
        {file ? (
          <button
            type="button"
            className="ac-hit mt-1 text-sm text-[var(--teal)] underline"
            onClick={(e) => {
              e.stopPropagation();
              onFile(null);
              setRejectMsg("");
            }}
          >
            Remove file
          </button>
        ) : null}
      </div>
      <input
        id={id}
        name="upload"
        type="file"
        accept={ACCEPT}
        className="sr-only"
        disabled={disabled}
        onChange={(e) => take(e.target.files)}
      />
      <p id={`${id}-hint`} className="mt-2 text-sm text-[var(--ink-muted)]">
        Or paste text above. At least one of paste or upload is required.
      </p>
      {rejectMsg ? (
        <p id={`${id}-reject`} role="alert" className="mt-2 text-sm text-[var(--crimson)]">
          {rejectMsg}
        </p>
      ) : null}
    </div>
  );
}
