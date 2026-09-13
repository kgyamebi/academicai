# Deployment Reliability Report — AcademicCheck AI

Date: 2026-09-09  

| Control | Status |
| --- | --- |
| `/api/ready` gate | Yes — deploy scripts wait on ready |
| `/api/live` liveness | Yes |
| Compose restart unless-stopped | Prod compose |
| `ops/rollback_compose.sh` | Script exists |
| Blue-green local proxy | `ops/cert_bluegreen.py` historical |
| Automatic rollback on failed ready | Tooling, **not** proven on hosted CD |
| Migration rollback | Dump restore, not alembic downgrade |
| Rolling multi-instance | Unproven (single compose typical) |

**PARTIAL** local deploy safety. **FAIL** production deployment reliability (hosted CD + auto-rollback evidence).
