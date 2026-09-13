# Circuit Breaker Report — AcademicCheck AI

Date: 2026-09-09  
Module: `backend/app/services/ai/circuit.py` (shared by AI, S3, billing, SMTP).

| Dependency | Open behavior | Proven |
| --- | --- | --- |
| openai / anthropic / gemini | Skip provider; try next; heuristic if all open | pytest + prometheus gauge |
| s3 | `StorageError` fail-fast | `test_s3_circuit_open_fails_fast` |
| stripe / paystack / flutterwave | HTTP 503 checkout | `test_billing_circuit_open_fails_without_provider_http` |
| smtp | Skip send (log) | `test_smtp_circuit_open_does_not_send` |

Half-open: cooldown then `allow()` True — `test_circuit_half_opens_after_cooldown` **PASS**.

## Limits

- In-process only (not Redis-shared). Multi-API-worker storms possible after restart.
- Threshold/cooldown from settings (`ai_circuit_threshold`, `ai_circuit_cooldown_seconds`).

**PASS** fail-fast circuits in pytest. **FAIL** distributed circuit / live provider-kill.
