# Runbook: Certificate failure / expiry

**SEV:** 2 if HTTPS broken; 1 if users bypass warnings or webhooks fail TLS.  
**Owner:** Platform (unassigned). **Alert:** A-CERT **not emitted** (no cert exporter).

## Detection

- Browser TLS errors; `curl` certificate verify fail
- Clients pin old cert
- No automated expiry page in this repo

## Impact

App unreachable; webhook delivery fail (looks like A-WH).

## Mitigation

Do not disable TLS verification on the API or workers.

## Recovery

1. Issue/renew at the cert provider (not automated here).
2. Reload LB / platform cert store (platform **not deployed** from this repo).
3. Confirm chain + hostname SAN.
4. DNS must still match (`dns-failure.md`).

## Escalation

SEV-2. Schedule renewal < 14 days is the **spec**; nothing measures it today.

## Validation

External TLS probe. Not run against production (no prod URL).

## Postmortem

SEV ≥ 2. Include expiry timestamps.
