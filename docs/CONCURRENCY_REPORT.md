# Concurrency Report — AcademicCheck AI

Date: 2026-09-09  

| Simulation | Result |
| --- | --- |
| Simultaneous identical webhooks | PASS (unique constraint / duplicate) |
| Duplicate HTTP webhook | PASS |
| Multiple purchases same idempotency window | Reuses pending / 409 if successful |
| Concurrent refunds | Cap + noop |
| Multi-tab | Time-bucketed keys — weak vs enterprise single-flight |

**PARTIAL PASS.** Strong on webhook races; weaker on multi-tab checkout exclusivity.
