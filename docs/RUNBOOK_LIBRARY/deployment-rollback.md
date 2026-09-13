# Runbook — Deployment rollback

## Symptoms
- Post-deploy ready failures, spike in 5xx, or bad release detected

## Diagnosis
1. Confirm deploy time and image tag
2. `GET /api/ready` and `/api/live`
3. Check recent logs for startup / migration errors

## Resolution
1. From repo root: `bash ops/rollback_compose.sh <previous_image_tag>`
2. Script recreates api/worker and **requires** `/api/ready` success
3. If ready still fails: `docker compose -f docker-compose.prod.yml logs api worker --tail=200`
4. Do not route traffic until ready is green

## Prevention
- Always deploy with `ops/deploy_compose.sh` (ready-gated)
- Keep previous tag recorded in the incident ticket

## Escalation
SEV-1 if rollback itself fails and customers are down.
