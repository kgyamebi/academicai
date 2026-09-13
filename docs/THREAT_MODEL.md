# Threat Model — AcademicCheck AI

Date: 2026-09-09  

## Assets

PII (email, name), assignment text, uploads, analysis reports, payment ledger, JWT/signing keys, PSP secrets, AI API keys, admin capability.

## Actors

Anonymous, registered student, guest, institution, admin, compromised refresh token holder, webhook forger, malicious upload author, prompt injector, curious co-tenant.

## STRIDE (condensed)

| Threat | Mitigations in repo | Residual |
| --- | --- | --- |
| Spoofing | Argon2id, MFA privileged, CSRF cookies | MFA staging UI open |
| Tampering | Ownership ORM, webhook HMAC, upload signatures | Live webhook unrun |
| Repudiation | security_events, admin audit | Hosted SIEM open |
| Info disclosure | 404 IDOR, field enc:v2, log redaction | Share link capability; dump custody |
| DoS | Rate limits, upload/size/page caps | Redis fail-closed prod |
| Elevation | RBAC + MFA gate admin | Pentest open |

## Data flows

Browser → API → Postgres / Redis / Storage / PSP / LLM. Workers read DB only for job authority.

## Assumptions (explicit)

- Operators deploy TLS terminator and secret manager (not proven here).
- Pytest isolation ≠ host CDN/cache isolation.
