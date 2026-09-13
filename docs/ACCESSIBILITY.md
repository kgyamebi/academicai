# Accessibility Audit Report — AcademicCheck AI

Date: 2026-09-07  
Standard requested: WCAG 2.2 AA  
Requested score: 98+  
**Certificate: not issued.** Evidence-backed score: **93 / 100**.

No product features were added. No UI redesign. No business-logic change. Invalid list markup and a billing error state were fixed because they would fail live axe.

## Blocker status

| # | Blocker | Result | Evidence |
| --- | --- | --- | --- |
| 1 | NVDA | **Fail — not executed** | No NVDA on this host |
| 2 | VoiceOver | **Fail — not executed** | macOS VoiceOver not available |
| 3 | JAWS | **Fail — not executed** | JAWS not installed; markup follows APG only |
| 4 | Authenticated dashboard live axe | **Pass (lab)** | Playwright axe on `/app/dashboard` |
| 5 | Authenticated report live axe | **Pass (lab)** | Playwright axe on populated report + score table |
| 6 | Admin live axe | **Pass (lab)** | Restricted student view and signed-in bootstrap admin overview |
| 7 | Lighthouse on deployed URL | **Fail** | Local `127.0.0.1:3111` only; not a production host |
| 8 | PDF PAC / Acrobat | **Fail** | Title/lang/extractable text proven; PAC and Acrobat Checker not run |

## Score rationale

Previous verified score: 90 (public axe only). This pass proved authenticated axe, keyboard/zoom/reflow lab checks, and PDF extractability. That is a real move to **93**. It is not 98: screen readers and a deployed Lighthouse URL remain unrun.

## Source defects closed this pass

| ID | Severity | Finding | Fix | Retest |
| --- | --- | --- | --- | --- |
| A19 | Medium | Dashboard/assignments put `<p>` inside `<ul>` | Empty states moved outside the list | Auth axe pass |
| A20 | Medium | Billing load failure stayed on “Loading…” | Error `role="alert"` when fetch fails | Auth axe pass |
| A21 | Medium | PDF lacked language / table / extract checks | Title, `/Lang`, score table, PyMuPDF extract test | `test_pdf_a11y.py` pass |

Critical: 0. High: 0 in source. Certification High: unrun AT.

Do not print “WCAG 2.2 AA compliant” on the product.
