# Queue Reliability Certification — AcademicCheck AI

Date: 2026-09-09  

| Bar | Result |
| --- | --- |
| Dedup / terminal skip / DuplicateJobError | **PASS** code + enqueue path |
| DLQ poison → fail_job | **PASS** pytest |
| Orphan heartbeat recover exactly once | **PASS** pytest |
| Worker startup requeue | **PASS** code (`recover_and_requeue_orphans`) |
| 1,000 analysis jobs 0 lost/dup | **PASS** historical `cert_queue_results.json` |
| Redis restart (volume retained) | **PASS** 2026-09-09 |
| Worker SIGKILL 12/12 zero stuck | **FAIL** `cert_worker_death.json` stuck=1 |
| 5k–50k analysis | **FAIL** ping-only / unrun |
| Redis volume wipe + full replay | **UNPROVEN** |

**FAIL** enterprise queue reliability. **PARTIAL PASS** for idempotent enqueue + orphan/DLQ in pytest.
