# Runbook: AI provider failure

**SEV:** 3 unless operators mistakenly halt core analysis. Heuristic path is independent.  
**Owner:** AI (unassigned). **Alert:** A-AI (`academiccheck_circuit`, `ai.provider_fail`). Unwired.  
**Evidence:** Pytest circuit only; chaos AI **not_run**.

## Detection

- Circuit `open` in `/api/metrics`
- Logs `ai` provider fail; enrich/coach errors
- Core scores still present

## Impact

Enrichment/coach degrade. Product must **not** invent LLM prose.

## Mitigation

Leave the circuit open. Do not raise timeouts to “make it work.” Do not paste student text into a personal ChatGPT session.

## Recovery

1. Check provider status / keys (secret manager).
2. `record_success` happens only on real OK — do not reset circuits in a REPL on prod to hide errors.
3. Resume when half-open probe succeeds.

## Escalation

SEV-3. Escalate to SEV-2 only if the API 5xx rate is actually from the provider path blocking requests (should not: fail closed to heuristic).

## Validation

Heuristic analysis completes. Circuit returns to `closed` only after successes.

## Postmortem

Optional SEV-3 unless users were told AI “graded” them incorrectly — then SEV-2 + integrity review.
