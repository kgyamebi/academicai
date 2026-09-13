# Database Reliability Certification — AcademicCheck AI

Date: 2026-09-09  

| Control | Status |
| --- | --- |
| Pool + pool_timeout | Compose / session kwargs |
| connect / statement / lock timeouts | **PASS** pytest inventory |
| SQLite refused in production | Startup check |
| Transaction rollback on HTTPException | FastAPI/SQLAlchemy session |
| Local dump → restore counts/fingerprints | **PASS** 2026-09-09 cert restore |
| Managed PITR / HA failover | **FAIL** |
| Deadlock retry loop | **Not a generic interceptor** — unique IntegrityError handled on billing/webhooks |
| Migration rollback | Restore dump, not `alembic downgrade` certified |

**PASS** local DB timeouts + logical restore. **FAIL** production database reliability (PITR/HA).
