# Alert rules and SLOs

These are specifications for the host (CloudWatch, Grafana, Datadog). They are not live until wired.

## SLOs (design targets, not measured)

| Service | SLO | Error budget / 30 days |
| --- | --- | --- |
| API availability (`/api/ready` true) | 99.9% | 43 minutes |
| Analysis job success (queued → completed) | 99.0% | 7.2 hours of failed-job time |
| Checkout start (configured providers) | 99.5% | 3.6 hours |
| p95 `/api/live` | < 200 ms | — |

## Alert rules

| Signal | Threshold | Action |
| --- | --- | --- |
| `http.5xx` rate | > 2% for 5 minutes | Page on-call |
| `/api/ready` false | 2 consecutive checks | Page on-call |
| RQ workers = 0 in production | 1 check | Page on-call |
| Webhook signature failures | > 20 / 5 minutes | Security review |
| Payment apply failures | > 0 unique after retry | Billing on-call |
| Queue age | > 10 minutes | Scale workers |
| AI provider errors | > 10% of enhanced jobs | Disable enhancement flag |

Do not treat this file as a performance certificate. Latency at 100–50,000 users has not been measured.
