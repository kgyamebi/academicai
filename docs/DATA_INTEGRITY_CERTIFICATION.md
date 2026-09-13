# Data Integrity Certification — AcademicCheck AI

Date: 2026-09-09  

| Domain | Duplicate / partial write protection | Proven |
| --- | --- | --- |
| Assignments / documents | Owner FK; no client IDs for authz | Isolation pytest |
| Analysis jobs | UUID PK; unique persist report per job | Isolation + runner |
| Findings | Created in job transaction | Restore counts |
| Credits | Ledger + grant fail-closed on drift | billing integrity pytest |
| Payments | Idempotency key + provider_event_id | sandbox pytest |
| Subscriptions | FSM illegal 409 | `test_billing_integrity_fsm.py` |
| Orphan jobs | Recover once then fail | pytest |

Partial writes: job crash → orphan recover or reaper fail + credit refund.  
Race: billing FOR UPDATE + unique constraints **PASS** sandbox.

**PASS** application integrity tests. **FAIL** if object storage lost (bytes ≠ dump).
