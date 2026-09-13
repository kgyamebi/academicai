# Timeout Certification — AcademicCheck AI

Date: 2026-09-09  
Evidence: `tests/test_reliability_hardening.py::test_timeout_inventory_external_calls_are_finite` **PASS**.

| Client | Connect / read | Statement / lock | Proven? |
| --- | --- | --- | --- |
| Postgres (psycopg) | `connect_timeout=3` | `statement_timeout=30000`, `lock_timeout=10000`; pool_timeout 30 | Source + pytest |
| Redis (API queue) | socket 2s / connect 2s | n/a | Source + pytest |
| Redis (worker) | 5s / 5s | n/a | Source + pytest |
| AI HTTP | `ai_timeout_seconds` (90) | n/a | Source + pytest |
| Stripe | http client timeout 15 | n/a | Source + pytest |
| Paystack/FLW | httpx timeout 15 | n/a | Source + pytest |
| SMTP | timeout=15 | n/a | Source + pytest |
| S3 | connect 5 / read 15 | n/a | Source + pytest |
| Alert webhook | urlopen timeout 5 | n/a | Source + pytest |
| Crossref | httpx 4.0 | n/a | Source review |
| ClamAV | socket 8s | n/a | Source review |

**PASS** finite timeouts in application clients (inventory).  
**FAIL** as a claim that no worker can hang: RQ `job_timeout=600` is a cap, not a proof under live stall; network partition chaos **not_run**.
