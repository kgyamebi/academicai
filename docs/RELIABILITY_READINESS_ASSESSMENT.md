# Reliability Readiness Assessment — AcademicCheck AI

Date: 2026-09-07

| Domain | Score / gate | Ready for paid student traffic? |
| --- | ---: | --- |
| Reliability (code + local chaos) | 93 / 98 | **No** |
| Queue (1k analysis) | certified that size only | **No** at 5k+ analysis |
| Workers (kill) | FAIL zero-stuck | **No** |
| Recovery | 74 local dump | **No** without PITR |
| DR | 74 | **No** |
| HA | FAIL SPOFs | **No** |
| Observability | 70 | **No** pager |
| Uptime | 18 (60 s window) | **No** |

**Overall: NOT READY.** Local laboratory reliability is high; enterprise HA/DR/alerting is not.
