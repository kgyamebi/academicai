# Dependency Resilience Report — AcademicCheck AI

Date: 2026-09-07  
Circuits: `backend/app/services/ai/circuit.py` (shared). Timeouts in clients. Live keys: **absent**.

| Dependency | Timeout | Circuit | Fallback | Host chaos |
| --- | --- | --- | --- | --- |
| OpenAI / Anthropic / Gemini | 90 s AI complete | per `provider.name` | next provider then `None` (heuristic core) | **not_run** (`ai_provider_kill`) |
| Stripe / Paystack / Flutterwave | 15 s | per provider | HTTP 503 checkout | **not_run** (`billing_provider_kill`); pytest HMAC |
| S3 / R2 | 5 s connect / 15 s read | `s3` | `StorageError` | **not_run** (`storage_kill`) |
| Internet / partition | — | — | — | **not_run** (`network_partition`) |
| Redis | 2 s | n/a | ready 503, enqueue false | **PASS** process stop |
| Postgres | 3 s connect | n/a | ready 503 | **PASS** process stop |
| SMTP | 15 s | smtp | fail-soft | pytest |

Process-local circuits **reset on restart** (not shared across replicas).

Graceful degradation: core analysis does not require LLM (**code**). Payments do not fake success (**code**). Uploads fail closed on S3 circuit (**code**).

## Verdict

**FAIL** live provider/storage/network matrix. **PASS** pytest isolation + Redis/PG process chaos.
