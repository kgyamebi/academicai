# Grafana dashboards — AcademicCheck AI

These JSON files are **import specifications** for a Prometheus-scraped Grafana.

**Not deployed.** No Grafana server, Prometheus server, or Alertmanager runs in this repository. Observability score does **not** increase because these files exist.

Import only after scraping `GET /api/metrics/prometheus` from each API replica.

Each dashboard `description` field records Owner, Purpose, Alert IDs, and Runbook paths (`docs/OBSERVABILITY_OPERATIONS.md`).

| Domain | File | Alert IDs | Runbooks |
| --- | --- | --- | --- |
| Infrastructure | `infrastructure.json` | A-READY, A-DB, A-REDIS | database / redis / high-error-rate |
| Database | `database.json` | A-DB | database / backup / restore |
| Queues | `queues.json` | A-QUEUE (depth only) | queue-backlog |
| Workers | `workers.json` | A-WORKER | worker-failure |
| Storage | `storage.json` | A-STORAGE **cannot fire** | storage-failure |
| Billing | `billing.json` | A-WH, A-PAY (incomplete) | billing / payment-webhook |
| AI systems | `ai.json` | A-AI | ai-provider-failure |
| Security | `security.json` | A-AUTH (logs) | security-incident / authentication |
| Business | `business.json` | none dedicated | billing-failure |
| Combined ops | `operations.json` | A-READY, A-5XX, A-LAT, A-QUEUE | high-error-rate / high-latency / queue-backlog |

Alert rules spec (also not loaded): `ops/prometheus/alert-rules.yml`.
