# Red Team Report — AcademicCheck AI

Date: 2026-09-07  
**FAIL.** No hired red team. No deployed-host adversarial engagement.

| Scenario | Lab pytest | Host |
| --- | --- | --- |
| Account takeover (stuffing) | lockout after 8 | unrun |
| Session hijacking (refresh reuse) | family revoke | unrun |
| Privilege escalation | guest/student ↛ admin | unrun |
| Cross-tenant | 404 matrix | **unrun = FAIL** |
| Injection SQL | ORM | unrun DAST |
| Prompt injection | 1000 synthetic | live model unrun |
| Payment abuse | HMAC / replay | live unrun |
| Webhook abuse | bad signature 400 | live unrun |

Do not present this file as a pentest. See `docs/PENETRATION_TEST_REPORT.md`.
