# Multi-Region DR Plan — AcademicCheck AI

Date: 2026-09-09  
Status: **Decision-ready configuration plan.** No secondary region is deployed. Remaining work is account provisioning, not design.

## Frozen topology (do not re-open)

| Role | Resource | Configuration (fill account IDs only) |
| --- | --- | --- |
| Primary | Region `PRIMARY_REGION` (choose and lock: `eu-west-1` **or** `us-east-1`) | Active API, RQ workers, primary Postgres, bucket `academiccheck-backups` |
| Secondary | Pair `eu-west-2` if primary is `eu-west-1`; else `us-west-2` | Warm API ASG desired=0, worker ASG desired=0, replica Postgres or PITR target, bucket `academiccheck-backups-dr` |
| DNS | Single zone, failover record | TTL **60 seconds**. Health check = `/api/live` on primary only (do not use `/api/ready` as the high-QPS probe — it stampedes DB+Redis) |
| Object CRR | `ops/s3_crr_replication.json` | Versioning ON both buckets. Prefix `backups/`. IAM role `academiccheck-s3-crr` |
| Secrets | Same names both regions | JWT, `BACKUP_ENCRYPTION_KEY`, PSP keys from the secret manager; never from disk dumps |

No additional regions, no active-active writes, no multi-master Postgres. Secondary is **warm standby**.

## Failure classes (closed decisions)

| Failure | Response | Who | Design RTO / RPO |
| --- | --- | --- | --- |
| Regional compute loss | Raise secondary ASG; flip DNS failover | On-call | RTO ≤ 2 h (unvalidated live) |
| Database failure | Promote replica **or** managed PITR into secondary; never restore onto old primary until fenced | DBRE | RPO ≤ 5 min if PITR enabled |
| Storage failure | Read from CRR destination; freeze uploads if checksum inventory mismatches | Platform | RPO = CRR lag |
| DNS failure | Lower TTL already 60s; manual CNAME to secondary LB | Infra | Minutes |

## Cutover checklist (when regions exist)

1. Declare SEV-0. Halt checkout if ledger risk (`docs/INCIDENT_RESPONSE.md`).
2. Fence primary: disable writer SG / take RDS out of DNS. Confirm it is not a brownout.
3. Promote DB or restore PITR to secondary. Verify `payments` / `subscriptions` counts vs last offsite dump manifest.
4. Point `STORAGE_BACKEND=s3` at the replica bucket. Freeze uploads if object inventory ≠ DB `documents.storage_key`.
5. Scale secondary API/workers. Confirm `/api/live` 200.
6. Flip DNS failover. Watch error rate 15 minutes.
7. Reconcile billing vs PSP **before** reopening checkout.
8. Reverse: rebuild primary as replica of new active; do not dual-write.

## What is not open

- Failover is DNS + ASG, not Anycast, not Kubernetes multi-cluster (unless later chosen as an implementation of this same topology).
- Redis: do not replicate the cert AOF across regions. Rebuild workers; recover jobs from Postgres `recover_orphaned_jobs`.
- Sessions: JWT is stateless; no sticky sessions required.

## Current reality

RTO/RPO for region loss: **not measured**. Apply this file when the live account exists.

## Verdict

**FAIL** multi-region resilience until the live pair is provisioned. The plan itself has no remaining design questions.
