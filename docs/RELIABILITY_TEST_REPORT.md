# Reliability Test Report — AcademicCheck AI

Date: 2026-09-07  
Do not treat “tests exist” as “drill passed.”

| Suite | Result | Evidence |
| --- | --- | --- |
| Unit / integration reliability | **PASS** pytest modules `test_reliability_hardening`, `injection`, `failures`, `queue_recovery` | Prior certification: 57 passed that cluster |
| Stress HTTP | **PARTIAL** | live_500 p95 3348 ms, errors 0; SLO fail |
| Soak | **FAIL unrun** | No multi-hour run artifact |
| Recovery tests | **PASS local PG dump** | `cert_restore_audit.json` |
| Chaos tests | **PARTIAL** | Redis/PG PASS; storage/AI/billing/network FAIL unrun |
| Queue tests | **PARTIAL** | 1000 analysis PASS; 50k FAIL unrun |
| Failover tests | **FAIL** | No managed failover |
| Regression | CI pytest floors 70/75 | `ci.yml` — not 98 reliability |

Isolation/billing pytest is **tenant correctness**, not HA.

## Verdict

Automated **code** paths are covered. Host reliability matrix is incomplete. **FAIL** as a complete reliability test program.
