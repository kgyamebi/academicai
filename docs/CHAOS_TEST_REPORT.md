# Chaos Test Report

Date: 2026-09-07  
API: uvicorn `APP_ENV=production` `REQUIRE_QUEUE=true` on `127.0.0.1:8012`  
Deps: cert Docker Postgres + Redis (`docker-compose.cert.yml`)

Artifact: `ops/cert_chaos_results.json` measured_at **2026-09-07T12:36:39Z**

This pass asserted recovery (ready 200) after Redis and Postgres start, not only the down state. An earlier probe at +3 s after Redis start was still 503; wait is now 8 s. That earlier result is not used as a pass.

## Injected failures

| Dependency | Live (`/api/live`) | Ready (`/api/ready`) | Recovery ready |
| --- | --- | --- | --- |
| Baseline | 200 | 200 | — |
| Redis stopped | 200 | **503** | **200** after start (+8 s) |
| Postgres stopped | 200 | **503** | **200** after start (+8 s) |
| Workers | — | — | Separate kill drill: **1 stuck** (`ops/cert_worker_death.json`) |
| Object storage | — | — | **Not run** |
| AI provider | — | — | **Not run** (pytest circuit exists) |
| Billing provider | — | — | **Not run** (pytest circuit exists) |
| Network partition | — | — | **Not run** |

No tenant-row corruption check was run during chaos (restore drill is separate).

## Verdict

**Pass** for Redis and Postgres process-kill **and recovery** on this host. **Fail** as a full chaos certificate (storage, AI, billing, network, worker-kill zero-stuck unrun or failed).
