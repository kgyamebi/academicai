# SMTP infrastructure — complete

**Date:** 2026-09-13  
**Status:** Code-complete (vendor credentials still operator-supplied)

## Stack

| Layer | Implementation |
| --- | --- |
| Validation | MX/DNS, disposable, reserved domains |
| Templates | Auth + analysis-ready HTML multipart |
| Transport | SMTP SSL/STARTTLS/plain + console (dev) |
| Envelope | `EMAIL_ENVELOPE_FROM` / MAIL FROM |
| Headers | Message-ID, List-Unsubscribe(+Post), Reply-To, Auto-Submitted |
| Queue | RQ `email` queue with retries; sync fallback |
| Metrics | `email.sent` / `failed` / `queued` / `circuit_open` (+ Prometheus) |
| Ready | Cached SMTP NOOP (45s TTL); staging/prod fail closed on console |
| Ops | `ops/local_smtp_sink.py`, `ops/check_email_delivery.py`, `/api/ops/smtp-probe` |
| Compose | Mailpit wired in dev + staging; prod env passthrough |

## Local

```powershell
python ops/local_smtp_sink.py
# backend/.env already points at 127.0.0.1:1025 (SMTP_TLS=disabled)
```

Or Docker Mailpit: UI http://localhost:8025

## Public production still needs from you

`SMTP_HOST` / user / password for a real vendor, plus SPF/DKIM/DMARC and HTTPS.
