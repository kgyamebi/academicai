# Scalability Gap Report — AcademicCheck AI

Date: 2026-09-07  
Scalability score remains **69 / 98**. Assumptions rejected.

| Area | Measured evidence | Classification |
| --- | --- | --- |
| Database | EXPLAIN p95 &lt; 10 ms at 100k assignments / 1M findings | PARTIAL |
| DB analytics GROUP | p95 124.7 ms after covering index | FAIL vs 100 ms |
| DB 5M/10M | Not loaded | FAIL (unrun) |
| HA replica | None | FAIL |
| Queues | 1000 analysis jobs; ping 5k/10k | PARTIAL |
| Workers horizontal | 1 and 5 workers local | PARTIAL |
| Storage | Local 10k; R2/S3/100k unrun | FAIL object scale |
| Document pipeline | Caps only; no size-tier bench | FAIL unrun |
| API `/api/live` 50 in-flight p95 | 490 ms (SLO 500) | PASS that probe |
| API `/api/live` 100 in-flight p95 | 1129 ms | FAIL |
| k6 100 VU p95 | 1879 ms | FAIL vs 500 ms |
| 1k–50k users | `not_run` | FAIL |
| Caching | Process AI cache | PARTIAL |
| AI architecture | Heuristic + optional LLM | PARTIAL |
| Horizontal API | 2 processes p95 1095 ms; 4 uvicorn in HTTP cert | PARTIAL |

No estimated cluster capacity. **Not** horizontally certified. Bottlenecks S1–S8 remain.
