# Secrets Management Report — AcademicCheck AI

Date: 2026-09-09  

| Control | Status |
| --- | --- |
| No live secrets in `backend/app` (literal scan) | PASS pytest |
| `.env` gitignored | Yes |
| `SECRETS_FILE` JSON inject allow-list | Implemented |
| `SECRET_MANAGER_URI` shape validation | Implemented (CSI mount pattern) |
| Production weak JWT/APP/FIELD keys refused | `assert_deployable_secrets` |
| AWS/GCP/Vault live wiring | **FAIL / HAL-08** |
| Backup encryption key allow-listed | Yes (`BACKUP_ENCRYPTION_KEY`) |

**FAIL** production secret manager certification. Architecture ready for CSI-mounted JSON.
