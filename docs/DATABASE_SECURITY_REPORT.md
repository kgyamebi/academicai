# Database Security Report — AcademicCheck AI

Date: 2026-09-09  

| Control | Status |
| --- | --- |
| Parameterized SQLAlchemy | Yes — no string-concat tenant IDs |
| ORM ownership filters | Yes |
| SQLite refused in production | Yes |
| Connection via DSN / PgBouncer compose | Yes |
| Role separation (DB users) | **App-level RBAC**; DB roles least-privilege **not proven** |
| Migration controls | Alembic; rollback = restore dump |
| Sensitive fields | AES-GCM when key set |
| Backup encryption | Optional AES-GCM envelope |
| Auditing | security_events / admin audit tables |

**PASS** application DB access patterns. **FAIL** DBA least-privilege / TDE certification.
