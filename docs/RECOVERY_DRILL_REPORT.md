# Recovery Drill Report — AcademicCheck AI

Date: 2026-09-09 (evening re-drill)

| Drill | Procedure | Timing | Success | Failure / residual | Lessons |
| --- | --- | ---: | --- | --- | --- |
| Database recovery | delete/DROP/migration/destroy + pg_restore + FK orphans | RTO **27.446 s** | Yes | Fingerprints ≠ full-row hash; PITR unrun | FK checks now part of pass criteria |
| Storage recovery | `verify_storage.py` delete/corrupt/restore | ~0.1 s restore | Yes | Not S3 | Fixture only |
| Redis restart | docker restart, AOF on | seconds | Yes | Volume wipe unrun | |
| Queue / orphan | pytest exactly-once | n/a | Yes | Worker-kill stuck historical | |
| Encrypted backup crypto | pytest round-trip | n/a | Yes | Prod offsite open | |
| Prod dump/restore | `PROD_DR_DRILL.md` | — | **Not run** | HAL-05b | Human required |
| Combined multi-system | — | — | **Not run** | | |

DR automation pytest this evening: **15 passed** (`test_dr_automation` + `test_prod_dr_safety` + orphan recover).
