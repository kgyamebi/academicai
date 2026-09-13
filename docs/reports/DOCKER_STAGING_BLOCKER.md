# Docker / staging bring-up blocker

**Host:** Windows 10 · Docker Client 29.7.2  
**Date:** 2026-09-13  

## Symptom

```
Error response from daemon: Docker Desktop is unable to start
```

Compose file ready: `docker-compose.staging.yml` (postgres, redis AOF, api, worker, web).

## Impact

Cannot prove on this machine:

- Redis healthy + workers ≥ 1 on `/api/ready`
- Containerized staging HTTPS
- Worker restart drill inside compose
- Full PUBLIC FREE LAUNCH certification

## Required operator action

1. Repair Docker Desktop (WSL2 backend / Hyper-V / restart) **or** provision cloud staging (Fly/Railway/Render/ECS).  
2. `docker compose -f docker-compose.staging.yml up -d --build`  
3. Export `STAGING_URL` + `STAGING_WEB_URL` + `SENTRY_DSN` + `NEXT_PUBLIC_SENTRY_DSN`  
4. `python ops/validate_public_launch.py`  
5. Confirm Sentry Issue for `academiccheck_sentry_probe_intentional`  
6. Re-issue `docs/reports/LAUNCH_CERTIFICATION.md`

Until then, certification remains **NO_GO** for public free launch.
