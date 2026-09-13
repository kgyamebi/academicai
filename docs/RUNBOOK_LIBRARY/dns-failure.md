# Runbook: DNS failure

**SEV:** 2 if web/API hostname fails; 1 if webhook DNS to PSP endpoints fails during paid traffic.  
**Owner:** Platform (unassigned). **Alert:** none in-app (A-NET not emitted).

## Detection

- Browser / `curl` NXDOMAIN or wrong IP
- PSP webhooks not arriving (looks like webhook failure)
- Certificate mismatch after a bad CNAME

## Impact

Users cannot reach the product. Webhooks may queue at PSP.

## Mitigation

Do not “fix” by pointing production at a personal tunnel without IC. Do not lower TTL experiments on the apex without a rollback IP.

## Recovery

1. Check registrar / DNS host (not in this repo).
2. Confirm A/AAAA/CNAME vs the intended LB (LB **not certified**).
3. Webhook URLs must match the public API host.
4. After DNS change: certificate (`certificate-expiry.md`).

## Escalation

SEV-2. SEV-1 if paid webhooks are landing on the wrong host.

## Validation

`curl -sS https://<host>/api/ready` from outside. Do not claim this was run for production — no prod host is attached.

## Postmortem

SEV ≥ 2. Include resolver evidence, not customer emails.
