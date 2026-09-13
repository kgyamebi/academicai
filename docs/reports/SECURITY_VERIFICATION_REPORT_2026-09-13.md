# Security Verification Report

**Product:** AcademicCheck AI (public free launch · billing disabled)  
**Date:** 2026-09-13  
**Evidence pack:** `ops/evidence/free_launch_verification_2026-09-13.json`  
**Gate:** 98+ with deployed-host proof  

## Verdict

| Metric | Score | Gate |
| --- | ---: | --- |
| Repo / unit security | **92 / 100** | — |
| Host / staging security | **UNPROVEN** | — |
| Evidence-backed combined | **88 / 100** | **98 FAIL** |

**Certification: NOT ISSUED** for public production host. Checkout intentionally disabled for free launch (reduces PSP attack surface; does not replace host hardening).

## Measured this pass

| Check | Result | Evidence |
| --- | --- | --- |
| Tenant isolation + hardening + document security + queue recovery + reliability circuits | **59/59 passed** | pytest pack 2026-09-13 (~161s) |
| Billing circuit open fails closed (503) | PASS after test arg fix | `test_reliability_hardening.py` |
| Checkout UI disabled | Purchases unavailable; no billing nav | product free-launch gate (prior pass) |
| Independent pentest | **Not run** | — |
| Secrets manager on staging | **Not verified** (`STAGING_URL` absent) | — |
| Sentry error capture | **DSN absent** in this environment | evidence JSON |
| Cookie Secure / HTTPS on host | **Not verified** | needs staging TLS probe |

## Findings

| ID | Severity | Finding | Status |
| --- | --- | --- | --- |
| SEC-S1 | **High** | No deployed-host isolation / IDOR replay | Open until staging pytest or smoke |
| SEC-S2 | **High** | No independent pentest on public URL | Open |
| SEC-S3 | **High** | Secrets / `APP_DEBUG` / `COOKIE_SECURE` unproven on host | Open |
| SEC-S4 | Medium | Admin MFA drill on staging not recorded | Open |
| SEC-S5 | Low | Billing providers unconfigured (acceptable for free launch) | Accepted |

## Path to 98 (measurable)

1. Staging HTTPS with `APP_DEBUG=false`, `COOKIE_SECURE=true`.  
2. Run isolation suite against staging API with two real users; 0 cross-tenant reads.  
3. Confirm security headers (`Strict-Transport-Security`, CSP as configured).  
4. Confirm upload rejects (EXE/EICAR/oversized) on staging.  
5. Pentest or scoped adversarial suite on staging URL — 0 Critical/High open.  
6. Attach evidence → re-score ≥98.

## Sign-off

Security 98+: **NO**  
Signed: _pending staging + pentest evidence_
