# SLO Report

Date: 2026-09-07  
Design targets remain in `docs/ALERTS_AND_SLOS.md`. Measured data only below.

| SLO | Target | Measured | Window |
| --- | --- | --- | --- |
| Ready availability | 99.95% | 1.0 | **60 s only** |
| Live availability | 99.95% | 1.0 | **60 s only** |
| API p95 | < 500 ms | k6 100 VU **1.87 s** | 3 min 2026-09-07 |
| Error rate | < 1% | 0% on live/ready k6 | 3 min |
| Analysis 1000 jobs success | 100% | 1000/1000 | one run |
| 7 / 30 / 90 day error budget | — | **not measured** | — |

Error budget remaining for 30-day 99.95%: **unknown**.
