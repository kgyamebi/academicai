# READINESS_VALIDATION_REPORT

**Measured:** 2026-09-13T21:20:27Z  
**STAGING_URL:** `http://127.0.0.1:8000`  

## Probes

| Check | Result |
| --- | --- |
| `/api/live` | {"ok": true, "status": 200, "json": {"status": "ok"}, "error": null} |
| `/api/ready` | {"ok": true, "status": 200, "json": {"status": "ok", "service": "AcademicCheck AI", "database": true, "redis": true, "workers": 1, "queue_depth": 0, "storage": true, "email": true, "queue_required": true, "sqlite": false, "ready": true, "env": "staging"}, "error": null} |
| Pass (db+redis+workers≥1) | **True** |

## Required ready fields

Database, Redis, workers, queue_depth, storage, email, queue_required, env — see evidence JSON.

## Architecture

See `docs/reports/STAGING_ARCHITECTURE.md`.
