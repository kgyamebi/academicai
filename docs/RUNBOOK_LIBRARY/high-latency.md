# Runbook: High latency

**SEV:** 2 if p95 `/api/live` > 500 ms at intended load (design).  
**Owner:** API (unassigned). **Alert:** A-LAT (process-local p95). Unwired.  
**Evidence:** live_50 p95 490 ms **pass**; live_100 p95 **1129 ms fail** (`ops/cert_http_results.json`). k6 100 VU p95 ~1879 ms.

## Detection

- `academiccheck_http_latency_ms{quantile="0.95"}`
- User “slow” reports
- Ready probes at 50 in-flight were ~2394 ms — do not use ready as a QPS probe

## Impact

UX degradation. Timeouts. Capacity **not** certified for launch load (OPS-08).

## Mitigation

Shed PDF (sync on API). Stop load tests against production. Do not raise DB timeouts as a fix.

## Recovery

1. Split paths: `/api/live` vs `/api/ready` vs report/PDF.
2. DB: slow queries; indexes 004–007.
3. Scale uvicorn workers / replicas (HTTP cert used 4 workers).
4. Redis/Postgres health.

## Escalation

SEV-2. Do not claim 1k–50k users.

## Validation

Bounded probe only. Compare to the cert JSON, not to an unmeasured SLO.

## Postmortem

SEV-2 if user-visible. Attach p95 samples and concurrency.
