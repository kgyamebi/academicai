# API Security Report — AcademicCheck AI

Date: 2026-09-09  

| Control | Status |
| --- | --- |
| Pydantic request schemas | Yes |
| Pagination caps (e.g. report page_size) | Yes |
| Rate limiting | Yes (Redis; fail-closed prod) |
| Upload / body size limits | Yes (settings) |
| CSRF on cookie mutations | Yes |
| Correlation IDs (`x-request-id`) | Yes |
| Secure errors (`{"error":...}` no stack) | Yes |
| OpenAPI disabled outside dev/test | Yes |
| Abuse metrics / webhook invalid | Yes |

**PASS repo API hardening.** Abuse detection is metric/event based — not a full WAF.
