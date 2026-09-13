#!/usr/bin/env python3
"""Copy Resend + Sentry settings from Invoice App into AcademicCheck local env.

Does not print secret values. Run once on your machine:

  python ops/import_invoice_email_sentry.py

Reads:  ../invoice app/invoiceapp/.env  (or INVOICE_ENV_PATH)
Writes: backend/.env  and  frontend/.env.local  (gitignored)
"""

from __future__ import annotations

import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INVOICE = Path(r"C:\Users\Administrator\Desktop\invoice app\invoiceapp\.env")


def _parse_env(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    if not path.is_file():
        raise SystemExit(f"Missing env file: {path}")
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        out[key.strip()] = value.strip().strip('"').strip("'")
    return out


def _upsert(path: Path, updates: dict[str, str]) -> list[str]:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = path.read_text(encoding="utf-8").splitlines() if path.is_file() else []
    seen: set[str] = set()
    new_lines: list[str] = []
    for line in lines:
        m = re.match(r"^([A-Za-z0-9_]+)=", line)
        if m and m.group(1) in updates:
            key = m.group(1)
            new_lines.append(f"{key}={updates[key]}")
            seen.add(key)
        else:
            new_lines.append(line)
    for key, value in updates.items():
        if key not in seen:
            new_lines.append(f"{key}={value}")
    path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
    return sorted(updates.keys())


def main() -> int:
    invoice_path = Path(os.environ.get("INVOICE_ENV_PATH") or DEFAULT_INVOICE)
    src = _parse_env(invoice_path)
    api_key = (src.get("EMAIL_API_KEY") or src.get("RESEND_API_KEY") or "").strip()
    sentry = (src.get("SENTRY_DSN") or src.get("NEXT_PUBLIC_SENTRY_DSN") or "").strip()
    email_from = (src.get("EMAIL_FROM") or "onboarding@resend.dev").strip()
    if not api_key:
        raise SystemExit("Invoice .env has no EMAIL_API_KEY / RESEND_API_KEY")
    if not sentry:
        raise SystemExit("Invoice .env has no SENTRY_DSN")

    backend_keys = _upsert(
        ROOT / "backend" / ".env",
        {
            "EMAIL_PROVIDER": "resend",
            "EMAIL_API_KEY": api_key,
            "EMAIL_FROM": email_from,
            "SENTRY_DSN": sentry,
            "EMAIL_ASYNC": "true",
            "EMAIL_SMTP_PROBE_ON_STARTUP": "true",
        },
    )
    front_keys = _upsert(
        ROOT / "frontend" / ".env.local",
        {
            "NEXT_PUBLIC_SENTRY_DSN": sentry,
            "NEXT_PUBLIC_SENTRY_ENVIRONMENT": "staging",
            "NEXT_PUBLIC_APP_ENV": "staging",
        },
    )
    print(f"Imported from: {invoice_path}")
    print(f"Updated backend/.env keys: {', '.join(backend_keys)} (values not printed)")
    print(f"Updated frontend/.env.local keys: {', '.join(front_keys)} (values not printed)")
    print("Restart API + worker + Next.js, then: python ops/check_email_delivery.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
