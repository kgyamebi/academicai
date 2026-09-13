# Billing Recovery Report — AcademicCheck AI

Date: 2026-09-09  

| Failure | Recovery | Proven? |
| --- | --- | --- |
| Webhook down / OOO | 503 leave unprocessed; PSP retry | PASS sandbox |
| Invalid signature | 400; no grant | PASS |
| Provider down | Checkout 503 / circuit | Code; live kill UNPROVEN |
| DB restart mid-webhook | Idempotent replay | PASS design + concurrent tests |
| Worker/queue restart | Billing is sync webhook-path | N/A for grants |
| Ledger drift | Grant blocked 409; reconcile | PASS unit |

**PASS** sandbox recovery paths. **FAIL** live provider-down chaos.
