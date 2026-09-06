# Security audit and residual risk

Date: 2026-09-06  
Method: code review against OWASP ASVS / Top 10. No live penetration test was executed in this pass.

## Controls now in the codebase

- Tenant ownership checks on assignments, documents, analysis, reports, PDF, share, compare, coach, billing
- Isolation tests fail the build on IDOR and privilege-escalation paths
- HttpOnly access/refresh cookies, refresh-family revoke on reuse, CSRF on cookie mutations
- Webhook signature verification (Stripe, Paystack, Flutterwave) plus replay table
- Field encryption prefix `enc:v1:`; production requires `FIELD_ENCRYPTION_KEY`
- OpenAPI disabled in production; staging admin-only
- Redis rate limits fail closed in production
- Security headers on API and Next.js responses, including CSP
- `security_events` + `/api/admin/security-events`
- Default admin bootstrap refused unless explicit long-password env vars are set

## Residual risk (not closed by this pass)

| Risk | Severity | Why it remains |
| --- | --- | --- |
| Live webhook/payment abuse against production keys | High until drill | Unit tests are not a pentest |
| Dependency CVEs | Medium | `pip-audit` is non-blocking in CI |
| Share-link guessing | Low | 24-byte urlsafe tokens; still public if leaked |
| LLM prompt injection residual | Medium | Firewall + 1000 injection cases exist; models can still leak style |
| Admin session on shared device | Medium | No hardware-key / step-up MFA |

## Threat model (short)

Attackers are other tenants, guests, unsigned webhook senders, and prompt-injection authors. Assets are drafts, reports, billing state, and admin flags. Trust boundaries are cookie/JWT auth, ownership queries, webhook signatures, and the AI firewall.

Honest security score: **hardened, not 95 until an independent pentest is attached**.
