# Privacy and Compliance Report — AcademicCheck AI

Date: 2026-09-07  
Not a legal opinion. Not GDPR/CCPA certification.

| Control | Implementation | Test / evidence | Residual |
| --- | --- | --- | --- |
| Retention | Guest `expires_at` purge with job reaper | pytest guest purge | Workers must run |
| Deletion | `DELETE /api/auth/me` anonymizes email, clears text, deletes storage bytes, local sub cancel, revoke sessions | engineering_quality / auth tests | PSP sub **not** cancelled (SEC-05); payment rows retained (stated) |
| Export | **no dedicated portable-export API** in this charter | — | **FAIL** as DSAR automation |
| Consent | Marketing/legal pages exist as product copy | — | Not re-audited as legal |
| Privacy controls | Isolation; field encryption when key set | isolation + crypto | Share links |
| Logs | redaction | logging.py | |

**PARTIAL** account deletion. **FAIL** automated export-request pipeline. **FAIL** provider subscription cancel on delete.
