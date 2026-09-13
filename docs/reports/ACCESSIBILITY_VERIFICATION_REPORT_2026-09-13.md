# Accessibility Verification Report

**Product:** AcademicCheck AI (public free launch · billing disabled)  
**Date:** 2026-09-13  
**Standard target:** practical WCAG 2.2 AA (do **not** claim certification)  
**Gate:** 98+ with deployed URL + AT evidence  

## Verdict

| Metric | Score | Gate |
| --- | ---: | --- |
| Static fixture axe | **100 / 100** (14/14 routes, 0 violations) | Lab only |
| Deployed Lighthouse a11y | **UNPROVEN** | — |
| Screen-reader recording | **UNPROVEN** | — |
| Evidence-backed combined | **87 / 100** | **98 FAIL** |

**Certificate: NOT ISSUED.** Do not print “WCAG AA compliant.”

## Measured this pass

| Check | Result | Evidence |
| --- | --- | --- |
| `node a11y/scan.mjs` | 14 fixtures, axe violations=0, serious=0, score=100 each | terminal 2026-09-13 |
| Lighthouse on `http://localhost:3001` | **Not completed** (run hung; no `a11y/artifacts/lighthouse-summary.json`) | evidence JSON |
| Playwright axe on staging | **Not run** (`STAGING_URL` absent; suite targets 127.0.0.1:3100) | `frontend/playwright.config.ts` |
| NVDA / VoiceOver / JAWS | **Not recorded** | — |

## Findings

| ID | Severity | Finding | Status |
| --- | --- | --- | --- |
| A11Y-S1 | **High** | No axe/Lighthouse evidence on deployed staging URL | Open |
| A11Y-S2 | **High** | No AT walkthrough recording | Open |
| A11Y-S3 | Medium | Authenticated report/dashboard a11y on staging unproven this pass | Open |
| A11Y-S4 | Low | Static fixtures are strong (0 violations) | Lab PASS |

## Path to 98 (measurable)

1. Set `LHCI_URL=$STAGING_URL` and `A11Y_LIGHTHOUSE_MIN=0.98`; require summary JSON all routes ≥0.98.  
2. `A11Y_BASE_URL=$STAGING_URL npx playwright test` (adapt config) — 0 serious axe.  
3. Record NVDA (Win) + VoiceOver (iOS/mac) on: Check → Report → Dashboard → Settings.  
4. Keyboard-only pass on staging; 44px targets; 320px reflow.  
5. Attach artifacts under `frontend/a11y/artifacts/` → re-score.

## Sign-off

Accessibility 98+: **NO**  
Signed: _pending deployed + AT evidence_
