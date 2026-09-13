# Reliability Certification — AcademicCheck AI

Date: 2026-09-09  
**Evidence-backed score: 94 / 100.** Gate **98**. **FAIL.**

Uptime 99.95%: **not attested** (60 s window only). Worker-kill zero-stuck: **FAIL**. Live provider kill: **FAIL**. Managed PITR: **FAIL**.

**LAUNCH NOT APPROVED** on reliability grounds.

## Mission bars

| Criterion | Result |
| --- | --- |
| No critical reliability issues remaining | **FAIL** REL-01 stuck job, REL-02 PITR |
| No high-severity remaining | **FAIL** REL-03–06 |
| No unrecoverable failure paths | **FAIL** object+PITR+region |
| No known data-loss paths | **FAIL** dump RPO + objects |
| No known duplicate-processing paths | **PASS** sandbox jobs/billing pytest |

## This pass (engineering)

RQ retry jitter; timeout inventory test; circuit half-open test. Does **not** close HAL-14/15.

## Required for 98

Zero-stuck worker death, billing/AI provider kill, managed PITR, multi-AZ/region, hosted alerting, multi-day uptime.
