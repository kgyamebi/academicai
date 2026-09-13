# Security Risk Register — AcademicCheck AI

Date: 2026-09-07  
Method: code + pytest. Score remains **92 / 98**. Gate 98. **FAIL.**  
Independent pentest: **not commissioned**. No issue below is “secure in production” without host evidence.

| ID | Class | Description | Root cause | Impact | Exploitability | Remediation |
| --- | --- | --- | --- | --- | --- | --- |
| SEC-01 | **Critical** | No independent pentest / DAST against a deployed host | Lab pytest ≠ ASVS pentest | Unknown Highs on the real stack | External attacker once DNS exists | Commission pentest; keep this FAIL until signed report with no open High |
| SEC-02 | **Critical** | Secrets not in a cloud secret manager | Env / optional `SECRETS_FILE` JSON mount only (`secrets.py`) | Key leak, failed rotation under incident | Anyone with host/env access | AWS SM / GCP SM / Vault + `ops/rotate-secrets.md` drill |
| SEC-03 | **High** | `pip-audit` in CI is non-blocking (`\|\| true`) | Workflow choice | Known CVEs can merge | Supply-chain | Blocking audit after triage; `security-scan.yml` is the intended gate |
| SEC-04 | **High** | No container image / Trivy scan | No image publish job | Vulnerable runtime | Supply-chain | Scan the deploy digest; do not claim SBOM without generating one in CI |
| SEC-05 | **High** | Account delete cancels **local** sub only | No PSP cancel API call | Provider may keep charging | Billing abuse / privacy | Cancel at Stripe/Paystack/FLW then local (needs keys — absent) |
| SEC-06 | **High** | No admin MFA | Out of product scope this charter | Admin session theft → all tenants | Stolen admin JWT | SSO/MFA (product) — **not added** |
| SEC-07 | **High** | Live webhook / PSP abuse untested | Keys absent | Double grant / replay in prod unknown | Network attacker on webhook URL | Staging PSP drill |
| SEC-08 | **High** | Backups are plaintext `pg_dump` | Script gzip only | Dump theft = full PII/ledger | Insider / backup disk | Encrypted offsite dumps |
| SEC-09 | **High** | Security monitoring does not page | Grafana/PD false | Isolation/auth abuse unseen | After detect window | Wire A-AUTH to pager |
| SEC-10 | **Medium** | ClamAV optional; fail-open in non-prod if unset | `clamav_host=""` | Malware in upload if AV down in dev | Upload | Set `CLAMAV_HOST` in prod (fail-closed if set and down) |
| SEC-11 | **Medium** | Share URL is a capability | Design | Anyone with token reads report | Link leak | Rotate/revoke share (exists); treat as secret |
| SEC-12 | **Medium** | Prompt injection residual | LLM may follow style | Integrity of AI comments | Uploaded essay | Firewall + wrap; not a formal proof against all models |
| SEC-13 | **Medium** | Field encryption skipped without key in non-prod | `encrypt_field` no-op | Dev DB plaintext | Dev leak | Prod requires `FIELD_ENCRYPTION_KEY` |
| SEC-14 | **Medium** | `security_events` not WORM | Ordinary table | Admin could alter history | Insider | Append-only store / SIEM export |
| SEC-15 | **Low** | CI uses SQLite | Speed | Dialect miss | Low | Optional PG in CI |
| SEC-16 | **Low** | CSRF exempts login/register | Need cookies before CSRF | Login CSRF | Browser | SameSite lax + rate limit |

## In-repo tests that did **not** find cross-tenant access

`tests/test_isolation.py` (assignments, documents, analysis, reports, PDF, coach, payments, subscriptions, versions, citations). **Host IDOR remains SEC-01.**

Unauthorized billing access: thief 404 on foreign payment/cancel — **pytest PASS**. Live **SEC-07**.
