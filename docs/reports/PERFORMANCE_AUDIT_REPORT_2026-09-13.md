# Performance Audit Report

**Product:** AcademicCheck AI (public free launch · billing disabled)  
**Date:** 2026-09-13  
**Evidence pack:** `ops/evidence/free_launch_verification_2026-09-13.json`  
**SLO reference (lab):** p95 &lt; 500 ms, error rate &lt; 1% (`ops/cert_http_results.json`)  

## Verdict

| Metric | Score | Gate |
| --- | ---: | --- |
| Evidence-backed performance | **80 / 100** | **98 FAIL** |

**Audit: NOT PASSED for 98.** Staging load unproven; historical lab SLO miss at 100 VU / 100 in-flight.

## Measured this pass (local API)

| Probe | Result |
| --- | --- |
| `/api/live` ×20 | avg **25.85 ms**, all observed OK |
| `/api/live` ×50 sequential | **49/50** OK; avg **493.3 ms** (degraded vs n=20) |
| Frontend `/` | HTTP 200 |
| `/api/metrics` | Exposed; `queue.workers=0`, `queue.depth=-1` |

## Historical lab evidence (2026-09-07)

| Artifact | Key numbers | vs SLO |
| --- | --- | --- |
| `ops/cert_http_results.json` | live in_flight=1 p95≈10 ms; in_flight=100 p95≈1129 ms | **live_100_meets_slo: false** |
| `ops/cert_k6_results.json` | 100 VU, 0% failed, p95≈**1879 ms**, checks 100% | **p95&lt;500 FAIL** |
| Queue throughput | 209.2 jobs/min @ 5 workers, 0 loss | Capacity OK in lab |

## Findings

| ID | Severity | Finding | Status |
| --- | --- | --- | --- |
| PERF-S1 | **High** | p95 SLO not met at 100 concurrent (lab) | Open until staging k6 pass or SLO revised + signed |
| PERF-S2 | **High** | No staging performance baseline | Open |
| PERF-S3 | Medium | Local live latency jumped under 50 sequential requests; 1 failure | Investigate connection reuse / server load |
| PERF-S4 | Medium | Workers=0 on local ready → analysis latency risk in free launch | Staging workers required |

## Path to 98 (measurable)

1. Staging baseline: p50/p95/p99 for `/api/live`, `/api/ready`, guest `/check` start, report GET.  
2. k6 profile 50 VU then 100 VU on staging; attach summary with error_rate &lt;1%.  
3. Decide free-launch SLO (e.g. p95&lt;800 ms for ready+live) and meet it — document in this report.  
4. Confirm CDN/cache headers for Next static assets on staging.  
5. Lighthouse performance category on staging `/` and `/check` (informational).  

## Sign-off

Performance 98+: **NO**  
Signed: _pending staging k6 + agreed SLO pass_
