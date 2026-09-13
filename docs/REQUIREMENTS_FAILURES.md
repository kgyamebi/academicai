# Requirements Failure Identification — AcademicCheck AI

Date: 2026-09-07  
Companion: `docs/REQUIREMENTS_TRACEABILITY_MATRIX.md`

## Missing (FAIL)

| ID | Root cause | Impact | Severity | Effort to fix |
| --- | --- | --- | --- | --- |
| REQ-72 Notifications | Model never wired | Users get no in-app analysis/credits events | Medium (product) | Medium — new API+UI (**product feature; not built this pass**) |
| REQ-92 Human review | Empty `reviewer_labels.jsonl`; no UI | Cannot claim human QC | High for AI claims | High — people + legal + UI |
| REQ-107 Ecosystem | Out of Phase 1 | No shared billing with sibling products | Low for first launch | High / other repos |

## Incomplete (PARTIAL — launch relevant)

| ID | Root cause | Impact | Severity | Effort |
| --- | --- | --- | --- | --- |
| REQ-31 versions | No rename/restore | History incomplete | Low | Small API |
| REQ-23 rubric upload | Paste only | Spec incomplete | Low | Upload pipeline reuse |
| REQ-28 Improve Sentence | Field unused | Mode missing | Low | Engine + UI |
| REQ-37/97 guest retention | Was field-only; **purge now exists** but only when reaper runs | Guest files linger if no workers | Medium | Cron/worker always-on in prod |
| REQ-38 training opt-in | Flag no toggle | Privacy control incomplete | Medium | Settings field |
| REQ-47 SSO | Prepare-only | Institution plan oversold if marketed | High if sold | Large |
| REQ-51/53 live billing | No PSP keys | Cannot take money safely | **Critical** | Live drills |
| REQ-61/62 workers in staging | Local Docker only | Lost jobs in prod | **Critical** | Staging workers |
| REQ-63 admin UI | Overview only | Ops cannot run the spec admin | Medium | Frontend |
| REQ-71 emails | Subset sent | Users miss receipts/complete mail | Medium | Templates + SMTP |
| REQ-73 a11y AA | AT unrun | Legal/exclusion | High | AT lab |
| REQ-91 AI gold | No lecturers | Over-claim risk | High | Human study |
| REQ-98 provider cancel | Local status only | Stripe sub may keep charging | High | Provider API |
| REQ-102 E2E | Paste-only pytest | Spec workflow unproven | High | Playwright E2E |

## Untested

Live PSP; DOCX upload E2E; coach content; weakest-area pytest; managed restore; NVDA; k6 authenticated; 5M rows.

## Undocumented vs spec

OpenAPI missing response models. Citation verify API undocumented because absent.

## Unverified in production

TLS, secret manager, Grafana, PITR, image scan, 99.9% SLO, blue-green on a real LB.

This pass **did** add pytest for guest purge and account-delete subscription cancel. That does not convert production FAILs to PASS.
