# Runbook: Authentication failure

**SEV:** 0/1 if session leak or mass takeover; 1 mass lockout; 2 login 503 (prod Redis rate-limit).  
**Owner:** Security (unassigned). **Alert:** A-AUTH — `refresh_reuse` / `security_events` **logs only**.

## Detection

- Login/refresh 401 vs 503
- Spike `http.4xx`
- `refresh_reuse` events
- Users locked out

## Impact

Cannot sign in; or sessions stolen (tenant data at risk).

## Mitigation

1. Distinguish 401 (credential/token) vs 503 (Redis rate-limit in production).
2. Do not email passwords. Reset tokens one-time.
3. Do not disable CSRF or JWT expiry “to restore access.”

## Recovery

1. Redis: `redis-failure.md` if 503.
2. Refresh reuse: family revoke must persist (`refresh_session` commits before 401).
3. Rotation: `JWT_SECRET_PREVIOUS` — `ops/rotate-secrets.md`.
4. Default admin `ChangeMeAdmin123!` disabled at startup if still present.

## Escalation

SEV-0/1 suspected takeover → security + IC + legal. Preserve `security_events`. Pentest still **FAIL** in this repo.

## Validation

Login, refresh, logout-all on a **test** account. Isolation pytest is not a live pentest.

## Postmortem

Required for SEV ≥ 1. No tokens in the document.
