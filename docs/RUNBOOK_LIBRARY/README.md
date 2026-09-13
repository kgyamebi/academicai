# Runbook library — AcademicCheck AI

Index of operator procedures. These do **not** imply a staffed on-call or deployed pager.

Severity: `docs/INCIDENT_RESPONSE_PLAN.md` (SEV-0–4).  
Command: `docs/INCIDENT_COMMAND_GUIDE.md`.  
Catalog: `docs/SERVICE_CATALOG.md`.  
Alerts: `docs/ALERT_CATALOG.md` (mostly unwired).  
On-call: `docs/ONCALL_OPERATIONS_GUIDE.md` (0 hours staffed).

Every runbook uses: Detection · Impact · Mitigation · Recovery · Escalation · Validation · Postmortem.

| Runbook | File |
| --- | --- |
| Postgres down | [database-failure.md](./database-failure.md) |
| Redis down | [redis-failure.md](./redis-failure.md) |
| Worker crash | [worker-failure.md](./worker-failure.md) |
| RQ queue backlog | [queue-backlog.md](./queue-backlog.md) |
| Storage failure | [storage-failure.md](./storage-failure.md) |
| AI provider failure | [ai-provider-failure.md](./ai-provider-failure.md) |
| Stripe failure | [stripe-failure.md](./stripe-failure.md) |
| Paystack failure | [paystack-failure.md](./paystack-failure.md) |
| Flutterwave failure | [flutterwave-failure.md](./flutterwave-failure.md) |
| Billing (umbrella) | [billing-failure.md](./billing-failure.md) |
| Webhook failure | [payment-webhook-failure.md](./payment-webhook-failure.md) |
| Authentication failure | [authentication-failure.md](./authentication-failure.md) |
| DNS failure | [dns-failure.md](./dns-failure.md) |
| Certificate failure | [certificate-expiry.md](./certificate-expiry.md) |
| High latency | [high-latency.md](./high-latency.md) |
| High error rate | [high-error-rate.md](./high-error-rate.md) |
| Data corruption | [data-corruption.md](./data-corruption.md) |
| Failed deployment | [deployment-failure.md](./deployment-failure.md) |
| Security incident | [security-incident.md](./security-incident.md) |
| Backup failure | [backup-failure.md](./backup-failure.md) |
| Restore failure | [restore-failure.md](./restore-failure.md) |

First probes (every runbook):

```
curl -sS -D- "$API/api/live"
curl -sS -D- "$API/api/ready"
curl -sS "$API/api/metrics" | head
```

Use `/api/ready` for load-balancer health. `/api/live` staying 200 during Redis/Postgres death is **by design** (`ops/cert_chaos_results.json`).
