# Billing Monitoring Report — AcademicCheck AI

Date: 2026-09-09  

| Signal | Mechanism |
| --- | --- |
| Failed payments | `billing.failed_payments` + `notify_payment_failure` |
| Webhook signature invalid | metric + alert |
| Successful / renewals / duplicates | counters |
| Ledger drift | `billing.ledger_drift` |
| Stale / missing webhook ts | metrics |
| Reconcile mismatch | `billing_reconcile_mismatch` alert |
| Abnormal refunds | txn trail; no dedicated anomaly ML |

Hosted Grafana scrape: HAL-10 open. Alert webhook/file: proven in alerting certs.
