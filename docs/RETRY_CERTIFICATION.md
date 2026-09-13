# Retry Certification Report — AcademicCheck AI

Date: 2026-09-09

| Path | Retry | Backoff | Limit | Duplicate protection | Failure tracking |
| --- | --- | --- | --- | --- | --- |
| AI HTTP `_post_json` | Yes | `wait_random_exponential` jitter | 2 | Cache key + job_id | circuit + metrics |
| AI providers | Fallback list | n/a | Configured set | Heuristic if all fail | per-name circuit |
| RQ analysis | Yes | 15/60/180 **+ jitter** | 3 | `job_id`, DuplicateJobError, terminal skip | DLQ |
| Paystack / Flutterwave checkout | **No HTTP retry** | n/a | 0 | Payment idempotency | Circuit |
| Stripe checkout | `max_network_retries=1` | Stripe | 1 | idempotency_key | Circuit |
| Webhooks | Provider on 503 | Provider | Provider | WebhookEvent unique | 503 |
| Email | None | n/a | 0 | n/a | SMTP circuit |
| S3 | botocore max_attempts 2 | AWS | 2 | UUID object key | Circuit |

Retries **must not** duplicate billing, jobs, or reports — sandbox pytest PASS. Live PSP retry: **UNPROVEN**.

Evidence: `test_rq_retry_intervals_are_jittered`, `test_ai_retries_use_jittered_backoff`, billing webhook replay tests.

**PASS** repository retry safety. **FAIL** live retry certification.
