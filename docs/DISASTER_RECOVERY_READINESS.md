# Disaster Recovery Readiness Assessment — AcademicCheck AI

Date: 2026-09-09  

## Score (honest)

| Category | Prior | Now | Gate | Pass? |
| --- | ---: | ---: | ---: | --- |
| Disaster recovery | 82 | **86** | 98 | **No** |

Δ: host-export restore 2/2, local WAL PITR 2/2, MinIO offsite 2/2, queue SIGKILL 0 lost 2/2, app storage `read_bytes` 2/2. Not raised for managed PITR, live S3, CRR apply, or human prod dump.

## Checklist

| Requirement | Status |
| --- | --- |
| Implemented recovery paths | Local/cert complete; prod pending account |
| Tested | Repeated local drills — `ops/cert_dr_repeat.json` |
| Documented | Yes |
| Monitored / alerted (backup fail) | Code yes; hosted scrape open |
| Automated where practical | MinIO + GHA scaffold + systemd units |
| Verifiable artifacts | `ops/cert_*.json` |

## Launch recommendation

**NO-GO for production launch on DR grounds.**

Local/cert recovery is evidenced and must not be confused with production DR certification.
