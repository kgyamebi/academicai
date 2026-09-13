# Email + Sentry setup (Invoice App parity)

AcademicCheck uses the same vendors as InvoiceFlow: **Resend** (HTTP API) and **Sentry**.

## One-shot import from Invoice App

```powershell
python ops/import_invoice_email_sentry.py
```

Copies `EMAIL_API_KEY`, `EMAIL_FROM`, and `SENTRY_DSN` into `backend/.env` and sets `NEXT_PUBLIC_SENTRY_DSN` in `frontend/.env.local`. Secrets are never printed.

Then restart API, worker, and Next.js.

## Providers

| `EMAIL_PROVIDER` | Behavior |
| --- | --- |
| `resend` | `POST https://api.resend.com/emails` with `EMAIL_API_KEY` (Invoice App pattern) |
| `smtp` | Classic SMTP (Mailpit / Brevo / Gmail) |
| `console` | Logs only — blocked in staging/production |

## Resend DNS (when you leave `onboarding@resend.dev`)

In Resend dashboard → Domains → add your domain, then:

- **SPF:** `v=spf1 include:_spf.resend.com ~all`
- **DKIM:** CNAMEs Resend shows you
- **DMARC:** start with `v=DMARC1; p=none; rua=mailto:you@yourdomain.com`

Set `EMAIL_FROM` to an address on that verified domain.

## Sentry

- Backend / worker: `SENTRY_DSN`
- Browser: `NEXT_PUBLIC_SENTRY_DSN` (same DSN is fine for one project, or split projects)
- Probe: `POST /api/ops/sentry-probe` with `x-ops-probe-token`

## Verify

```powershell
python ops/check_email_delivery.py
python ops/check_email_delivery.py --send you@your-inbox.com
```
