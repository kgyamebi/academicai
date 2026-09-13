# API Resilience Report — AcademicCheck AI

Date: 2026-09-07  
Chaos: Redis/PG. Load: `cert_http_results.json`. Pytest: `test_reliability_*.py`.

| Control | Status | Validated? |
| --- | --- | --- |
| Graceful shutdown | uvicorn default; compose `restart: unless-stopped` | **Not** a drain-tested shutdown |
| Request timeouts | Frontend abort 60s / 180s upload; DB 30s | Frontend **not Playwright-proved** |
| Circuit breakers | AI, S3, stripe/paystack/flutterwave, SMTP | Pytest fail-fast |
| Retry policies | AI jittered 2 attempts; Stripe max_network_retries=1 | Pytest; live unrun |
| Rate limiting | Redis in production | Fail-closed if Redis down (prod) |
| Backpressure | enqueue false; ready 503 | Pytest + chaos |
| Overload | live_100 p95 1129 ms, **0% errors** | Latency FAIL SLO; errors PASS |
| Health / ready | `/api/live`, `/api/ready` | Chaos PASS |

## Requested validations

| Scenario | Result |
| --- | --- |
| Traffic spikes | 500 in-flight live p95 3348 ms, error 0 — **degrades slowly, not shed** |
| Dependency failures | Redis/PG → live 200, ready 503 | **PASS** |
| Provider failures | Pytest circuits | Host **not run** |
| Network latency | **Not run** |
| Slow database | statement_timeout 30s | **Not injected** |

## Verdict

Fail-closed on Redis/PG is proven. Overload protection is **not** admission-control (no 429 on CPU). **PARTIAL.**
