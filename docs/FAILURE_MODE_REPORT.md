# Failure Mode Report — AcademicCheck AI

Date: 2026-09-07  
Chaos artifact: `ops/cert_chaos_results.json` (Redis/Postgres process kill).  
Pytest: `tests/test_reliability_injection.py`, `test_reliability_failures.py`, `test_reliability_hardening.py`.

## Required scenario tests

| Scenario | Impact | Detection | Recovery | Automation | Evidence |
| --- | --- | --- | --- | --- | --- |
| Database unavailable | Writes fail; ready 503; live 200 | `/api/ready` database=false | Restart Postgres; pool_pre_ping | Compose restart | Chaos 12:36:39Z live 200 / ready 503 / recover **200** |
| Redis unavailable | Queue + prod rate-limit 503; live 200 | `/api/ready` redis=false when REQUIRE_QUEUE | Restart Redis; fail-closed enqueue | Compose restart | Chaos 12:36:39Z; +3 s recover was 503, +8 s **200** |
| Worker unavailable | Enqueue false; analysis 503 in prod | queue_has_no_workers log; workers gauge (metrics only) | Start RQ worker | Manual / compose | Pytest; host 1000-job prior |
| Storage unavailable | Upload 4xx/5xx; analysis cannot read | StorageError; s3 circuit open | Restore disk/S3; circuit cooldown 30 s | None | Local disk 1k/10k files prior; **S3 kill not run** |
| AI provider outage | Heuristic analysis continues; no LLM enrich | ai.provider_fail; circuit open | Fallback providers then None | Circuit + fallback | Pytest circuit; **live LLM not run** |
| Payment provider outage | Checkout 503; no charge | Circuit / 502 from PSP | User retry; webhook 503 until payment row exists | Circuit fail-fast | Pytest circuit; **live PSP not run** |
| Email provider outage | Register still succeeds | email_send_failed / email_circuit_open | Retry later (no queue) | Fail-soft + SMTP circuit | Pytest; **SMTP host not run** |
| Network latency | Timeouts fire; no infinite wait | httpx/SMTP/S3/DB timeouts | Retry with jitter (AI only) | Timeouts listed in Timeout Audit | Code + pytest source assertions; **partition not injected** |
| Partial degradation | Ready 503, live 200 | Ready vs live split | Keep serving liveness; stop ready traffic | Load balancer should use `/api/ready` | Chaos |

## Cascading-failure notes

- Process-local circuits do **not** coordinate across API replicas. Five failures per process still required to open.
- Billing checkout does **not** auto-retry HTTP (prevents duplicate Paystack/Flutterwave initialize). Stripe `max_network_retries=1` with payment `idempotency_key`.
- RQ Retry 3× can replay analysis; persist guard returns existing report (`job_id` unique).

## Verdict

FMEA for **Postgres and Redis process death** is evidenced on this host. Storage, AI, billing, email, and network-partition rows are **code-path only**. Not a full chaos certificate.
