# Tenant Isolation Certification — AcademicCheck AI

Date: 2026-09-09  
Suite: `tests/test_isolation.py`, `test_hardening.py`, `test_security_lab_attacks.py`, MFA/admin tests.  
Executed this pass: **69** related security tests green (core suite 2026-09-09) + lab attacks.

| Attack simulation | Result |
| --- | --- |
| User A → User B assignment/document/analysis/report/PDF/coach | 404 |
| User A → User B payment / subscription cancel | 404 |
| User A credits/billing JSON | own data only |
| Student/guest → admin | 403 |
| Share mint/revoke cross-tenant | denied |

**Repository isolation: PASS (100 in prior gate language for pytest-only).**  
**Production isolation: FAIL** until host pentest — CDN/cache/race not covered.
