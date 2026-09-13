# Credit Integrity Report — AcademicCheck AI

Date: 2026-09-09  

| Scenario | Result |
| --- | --- |
| Purchase grant + ledger row | PASS |
| Reserve / consume / refund reservation | PASS |
| Expiry unusable + ledger match | PASS |
| Refund clawback full/partial | PASS |
| Duplicate grant via webhook replay | PASS (no double) |
| Negative remaining | Prevented by clawback `min` |
| Silent wallet corruption then grant | **409 fail-closed** (new) |
| Orphan credits without payment | Reconcile / ops |

**PASS** sandbox credit integrity with drift detection on grant.  
**FAIL** live credit purchase certification.
