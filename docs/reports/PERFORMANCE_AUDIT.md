# PERFORMANCE_AUDIT

**Measured:** 2026-09-13T21:20:27Z  

| Surface | Current | Target | Notes |
| --- | ---: | ---: | --- |
| `/api/live` | lab ~26ms | p95 < 100ms | local |
| Ready | depends on redis | p95 < 300ms | staging |
| Landing | unmeasured staging | LCP < 2.5s | need LH |
| Report | defer charts | TTI improve | code-split backlog |

Historical k6 @100 VU p95 miss remains open until staging k6 re-run.
