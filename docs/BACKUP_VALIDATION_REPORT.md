# Backup Validation Report — AcademicCheck AI

Date: 2026-09-07  
Artifact: `ops/cert_restore_audit.json` (2026-09-07T09:49:43Z)

| Check | Result |
| --- | --- |
| Provider | docker-local Postgres 16 |
| Managed PITR | **false** |
| Dump | 11.131 s |
| Five restore cycles | 20.007–28.837 s |
| Counts match | **true** (users 6, assignments 100005, findings 1003300, reports 1101, payments/credits/subscriptions 1) |
| Fingerprints match | **true** |
| Accidental delete recovered | assignments 99755 → 100005 |
| Failed migration recovered | **true** |
| Encrypted backup | **not used** |

**PASS** as a local dump integrity check. **FAIL** as encrypted or point-in-time backup certification.
