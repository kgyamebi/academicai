# RPO / RTO Certification — AcademicCheck AI

Date: 2026-09-09  
Rule: design targets ≠ SLAs. Measured values cite artifacts only.

| Service | Design RTO | Design RPO | Measured RTO | Measured RPO | Certified? |
| --- | --- | --- | --- | --- | --- |
| PostgreSQL (local Docker) | 60 min managed | 5 min PITR | **27.446 s** destroy-restore (2026-09-09T20:22:38Z) | Last custom dump | Local **YES**; managed **NO** |
| Object storage (local) | unset | unset | <1 s fixture restore | Last checksummed tree | Local fixture **YES**; S3 **NO** |
| Redis | unset | AOF | Restart seconds | Volume retained | Restart **YES**; wipe **NO** |
| Queues / jobs | unset | DB job row | Orphan recover pytest | DB state | Partial |
| Payments (ledger rows) | follow PG | follow PG | with PG restore | Last dump | Local seed **YES**; live PSP **NO** |
| Reports (DB) | follow PG | follow PG | with PG restore | Last dump | Local **YES** |
| Assignments | follow PG | follow PG | with PG restore | Last dump | Local **YES** |
| Region failover | 2 h design | 5 min design | **not measured** | **not measured** | **NO** |

## Achievability

- Local logical RTO ~52 s is **achievable on cert host** for this dataset (~100k assignments / ~1M findings).
- Production RTO/RPO with managed PITR: **not validated**.
- Do not publish design 5-minute RPO as a customer commitment.

## Verdict

**FAIL** production RPO/RTO certification.  
**PASS** documentation of measured local objectives only.
