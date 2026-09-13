# Infrastructure Security Report — AcademicCheck AI

Date: 2026-09-09  

| Control | Status |
| --- | --- |
| HTTPS / HSTS | App sets HSTS in prod; terminator **unproven** |
| CSP / X-Frame / XCTO / Referrer-Policy | API + Next headers |
| Private Redis/Postgres in compose | Yes (network) |
| Security groups / cloud firewall | **Host — unproven** |
| Admin isolation | Role + MFA; no separate admin network |
| OpenAPI off in prod | Yes |

**PARTIAL.** Cloud network segmentation evidence: **FAIL**.
