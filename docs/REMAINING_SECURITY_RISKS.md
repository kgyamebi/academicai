# Remaining Security Risks — AcademicCheck AI

Date: 2026-09-09  

| ID | Severity | Risk | Status |
| --- | --- | --- | --- |
| SEC-01 | Critical | No independent pentest | Open HAL-07 |
| SEC-02 | Critical | Secret manager not proven in prod | Open HAL-08 |
| SEC-03 | Critical | Live PSP webhook abuse unproven | Open HAL-01–03 |
| SEC-04 | High | ClamAV not **mandatory** in prod | Open HAL-12 (code wired; config flip) |
| SEC-05 | High | Main CI pip-audit non-blocking | **Closed** this pass |
| SEC-07 | High | Production TLS cert / SSL Labs | Open HAL-19 (app/local TLS proven) |
| SEC-06 | High | MFA staging/UI drill | Code done; HAL-09 open |
| SEC-08 | High | Offsite dump custody / prod encrypt ops | Partial (crypto + rotation grace exist) |
| SEC-09 | Medium | Register first-session | Open |
| SEC-10 | Medium | Prompt injection residual | Inherent (indirect cases now tested) |
| SEC-11 | Medium | Share capability URL | Accepted product risk |
| SEC-12 | Low | Dual backup formats | Open |

Items that still **require a live account or external party**: pentest (HAL-07), secret manager (HAL-08), live PSP (HAL-01–03), ClamAV production mandate (HAL-12), live-domain TLS/SSL Labs (HAL-19). Everything else in the 2026-09-09 security-extended pass is code-proven.

Closed/reduced this pass: CI pip-audit swallow (HAL-24/SEC-05); SBOM/license/pins; malware quarantine path; local TLS 1.2+; container non-root + prod network ports; expanded adversarial + Hypothesis; indirect prompt injection; key-rotation grace period.
