# Accessibility checklist and compliance report

Date: 2026-09-06  
Standard: WCAG 2.2 AA  
Scope: existing AcademicCheck AI UI only. No new product surfaces.

## What was remediated

- Skip link and `lang="en"` on the root document
- Visible mobile primary navigation with `aria-expanded` / `aria-controls`
- `aria-current="page"` on app and marketing navigation
- Form controls have visible labels, `id`/`htmlFor`, autocomplete, `aria-invalid`, and `role="alert"` errors
- Sign-out and report actions use `type="button"`
- Editor toolbar exposes `role="toolbar"` and `aria-pressed`
- Score ring remains a numeric `role="img"` (not color-only)
- Structure map uses text status, not symbols alone
- Contrast token `--ink-muted: #314057` on `--paper: #f6f3ec` (estimated ≥ 7:1)

## Automated checks

`backend/tests/test_a11y_static.py` fails CI if buttons lack an explicit `type`, or if the skip link / language / contrast token disappear.

## Remaining work before a 95 score can be claimed

These are not signed off in this pass:

- Third-party axe / Lighthouse audit on a deployed build
- Screen-reader walkthrough (NVDA, VoiceOver, TalkBack) of check → report → billing
- Focus restore after the analysis polling state and after share-password dialogs
- Full 2.2 AA contrast measurement of every Tailwind opacity utility still in older pages
- Mobile reflow at 320px for every authenticated assignment sub-page

Honest current score: **improved, not certified**. Treat production accessibility as **open** until the remaining walkthroughs are recorded.
